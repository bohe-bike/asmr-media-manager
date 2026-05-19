import os
import re
import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.author_rule import AuthorRule
from app.models.media import Media

logger = logging.getLogger(__name__)


class AuthorMatcher:
    """作者关键词匹配服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._rules_cache: list[AuthorRule] | None = None
        self._cache_loaded_at: datetime | None = None

    async def match(self, media: Media) -> dict | None:
        """对单个媒体执行作者匹配，返回匹配结果或 None"""
        texts = self._collect_match_texts(media)
        rules = await self._get_enabled_rules()

        for rule in rules:
            for target, text in texts.items():
                if not text:
                    continue
                if self._match_rule(rule, text):
                    await self._record_hit(rule)
                    return {
                        "creator": rule.creator,
                        "circle": rule.circle,
                        "cv": rule.cv,
                        "matched_keyword": rule.keyword,
                        "matched_target": target,
                        "rule_id": rule.id,
                    }
        return None

    def _collect_match_texts(self, media: Media) -> dict:
        """收集所有可用于匹配的文本"""
        texts = {"filename": media.file_name, "directory": ""}
        if media.file_path:
            texts["directory"] = os.path.basename(os.path.dirname(media.file_path))
        if media.creator:
            texts["metadata_artist"] = media.creator
        if media.title:
            texts["metadata_album"] = media.title
        return texts

    def _match_rule(self, rule: AuthorRule, text: str) -> bool:
        """根据规则类型执行匹配"""
        if not text:
            return False
        try:
            if rule.match_type == "contains":
                return rule.keyword in text
            elif rule.match_type == "exact":
                return rule.keyword == text
            elif rule.match_type == "prefix":
                return text.startswith(rule.keyword)
            elif rule.match_type == "suffix":
                return text.endswith(rule.keyword)
            elif rule.match_type == "regex":
                return bool(re.search(rule.keyword, text))
        except re.error:
            logger.warning(f"Invalid regex pattern in rule {rule.id}: {rule.keyword}")
        return False

    async def _record_hit(self, rule: AuthorRule) -> None:
        """记录规则命中次数和时间"""
        rule.hit_count += 1
        rule.last_hit_at = datetime.utcnow()
        await self.db.commit()

    async def _get_enabled_rules(self) -> list[AuthorRule]:
        """获取已启用的规则，按优先级降序排列（带缓存）"""
        now = datetime.utcnow()
        if (
            self._rules_cache is None
            or self._cache_loaded_at is None
            or (now - self._cache_loaded_at) > timedelta(seconds=300)
        ):
            result = await self.db.execute(
                select(AuthorRule)
                .where(AuthorRule.enabled == True)
                .order_by(AuthorRule.priority.desc())
            )
            self._rules_cache = list(result.scalars().all())
            self._cache_loaded_at = now
        return self._rules_cache

    async def apply_to_existing(
        self,
        rule_ids: list[int] | None = None,
        overwrite: bool = False,
    ) -> dict:
        """将规则应用到已有媒体记录"""
        stats = {"total_checked": 0, "newly_classified": 0, "skipped": 0, "overwritten": 0}

        query = select(Media)
        if not overwrite:
            query = query.where(Media.creator.is_(None))

        result = await self.db.execute(query)
        medias = result.scalars().all()

        for media in medias:
            stats["total_checked"] += 1
            match_result = await self.match(media)
            if match_result:
                if media.creator and not overwrite:
                    stats["skipped"] += 1
                    continue
                if media.creator and overwrite:
                    stats["overwritten"] += 1
                else:
                    stats["newly_classified"] += 1
                media.creator = match_result["creator"]
                media.circle = match_result["circle"]
                media.cv = match_result["cv"]

        await self.db.commit()
        return stats
