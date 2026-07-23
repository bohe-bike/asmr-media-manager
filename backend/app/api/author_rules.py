from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.author_rule import AuthorRule
from app.models.media import Media
from app.schemas.author_rule import (
    AuthorRuleCreate,
    AuthorRuleUpdate,
    AuthorRuleResponse,
    AuthorRuleListResponse,
    BatchAuthorRuleCreate,
    ScanTestResponse,
    ApplyRequest,
    ApplyResponse,
)
from app.schemas.common import ApiResponse
from app.services.author_matcher import AuthorMatcher
from app.core.exceptions import NotFoundException

router = APIRouter()


@router.get("/author-rules", )
async def list_author_rules(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    creator: str | None = None,
    circle: str | None = None,
    keyword: str | None = None,
    enabled: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    """获取作者规则列表"""
    query = select(AuthorRule)
    if creator:
        query = query.where(AuthorRule.creator.contains(creator))
    if circle:
        query = query.where(AuthorRule.circle.contains(circle))
    if keyword:
        query = query.where(AuthorRule.keyword.contains(keyword))
    if enabled is not None:
        query = query.where(AuthorRule.enabled == enabled)

    # Count
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()

    # Paginate
    query = query.order_by(AuthorRule.priority.desc(), AuthorRule.id.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    rules = result.scalars().all()

    return ApiResponse(data=AuthorRuleListResponse(
        items=[AuthorRuleResponse.model_validate(r) for r in rules],
        total=total,
        page=page,
        page_size=page_size,
    ))


@router.post("/author-rules", )
async def create_author_rule(
    request: AuthorRuleCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建作者规则"""
    rule = AuthorRule(
        keyword=request.keyword,
        match_type=request.match_type,
        match_target=request.match_target,
        creator=request.creator,
        circle=request.circle,
        cv=request.cv,
        priority=request.priority,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return ApiResponse(data=AuthorRuleResponse.model_validate(rule))


@router.post("/author-rules/batch", )
async def batch_create_author_rules(
    request: BatchAuthorRuleCreate,
    db: AsyncSession = Depends(get_db),
):
    """批量创建作者规则"""
    rules = []
    for r in request.rules:
        rule = AuthorRule(
            keyword=r.keyword,
            match_type=r.match_type,
            match_target=r.match_target,
            creator=r.creator,
            circle=r.circle,
            cv=r.cv,
            priority=r.priority,
        )
        db.add(rule)
        rules.append(rule)

    await db.commit()
    for rule in rules:
        await db.refresh(rule)

    return ApiResponse(data=[AuthorRuleResponse.model_validate(r) for r in rules])


@router.post("/author-rules/scan-test", )
async def scan_test_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
):
    """测试规则匹配效果"""
    result = await db.execute(select(AuthorRule).where(AuthorRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise NotFoundException(f"规则 {rule_id} 不存在")

    matcher = AuthorMatcher(db)
    medias_result = await db.execute(select(Media))
    medias = medias_result.scalars().all()

    matched = 0
    samples = []
    for media in medias:
        texts = matcher._collect_match_texts(media)
        for target, text in matcher.get_target_texts(rule, texts):
            if text and matcher._match_rule(rule, text):
                matched += 1
                if len(samples) < 10:
                    samples.append({
                        "file_name": media.file_name,
                        "matched_text": text,
                        "match_source": target,
                    })
                break

    return ApiResponse(data=ScanTestResponse(
        total_media=len(medias),
        matched_media=matched,
        samples=samples,
    ))


@router.post("/author-rules/apply", )
async def apply_rules(
    request: ApplyRequest,
    db: AsyncSession = Depends(get_db),
):
    """将规则应用到已有媒体"""
    matcher = AuthorMatcher(db)
    stats = await matcher.apply_to_existing(request.rule_ids, request.overwrite)
    return ApiResponse(data=ApplyResponse(**stats))


@router.patch("/author-rules/{rule_id}", )
async def update_author_rule(
    rule_id: int,
    request: AuthorRuleUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新作者规则"""
    result = await db.execute(select(AuthorRule).where(AuthorRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise NotFoundException(f"规则 {rule_id} 不存在")

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)

    await db.commit()
    await db.refresh(rule)
    return ApiResponse(data=AuthorRuleResponse.model_validate(rule))


@router.delete("/author-rules/{rule_id}")
async def delete_author_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    """删除作者规则"""
    result = await db.execute(select(AuthorRule).where(AuthorRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise NotFoundException(f"规则 {rule_id} 不存在")

    await db.delete(rule)
    await db.commit()
    return ApiResponse(message="规则已删除")
