import asyncio
import logging
import re
import time
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

# 语言检测关键字 → language 字段映射
_LANG_MAP = {
    "日本語": "ja",
    "中文": "zh",
    "English": "en",
}


class DlsiteService:
    """DLsite API 服务：根据 RJ/DL 号获取作品元数据"""

    def __init__(self):
        self._settings = get_settings()
        self._cache: dict[str, tuple[float, dict]] = {}
        self._last_request_time: float = 0.0

    @property
    def enabled(self) -> bool:
        return self._settings.dlsite_enabled

    async def fetch_by_id(self, work_id: str) -> dict[str, Any] | None:
        """根据 RJ/DL 号获取作品信息，返回结构化数据或 None。

        work_id 格式：RJ123456 或 DL123456（大小写不敏感）
        """
        if not self.enabled:
            return None

        work_id = work_id.upper().strip()
        if not re.match(r'^(RJ|DL)\d{6,8}$', work_id):
            return None

        # 检查缓存
        ttl = self._settings.dlsite_cache_ttl
        if work_id in self._cache:
            ts, data = self._cache[work_id]
            if time.time() - ts < ttl:
                return data
            del self._cache[work_id]

        # 限流
        await self._rate_limit()

        # 尝试请求，失败时降级到旧 API
        data = await self._fetch_product(work_id)
        if data is None:
            data = await self._fetch_product_legacy(work_id)

        if data:
            self._cache[work_id] = (time.time(), data)
        return data

    async def _fetch_product(self, work_id: str) -> dict[str, Any] | None:
        """通过主 API 获取作品信息"""
        base = self._settings.dlsite_api_base.rstrip("/")
        # 去掉 RJ/DL 前缀，API 只接受纯数字
        num_part = re.sub(r'^(RJ|DL)', '', work_id)
        url = f"{base}/=/product.json?workno={num_part}"

        try:
            async with httpx.AsyncClient(
                timeout=self._settings.dlsite_timeout,
                proxy=self._settings.dlsite_proxy or None,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://www.dlsite.com/",
                },
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                raw = resp.json()

            # DLsite API 返回数组，取第一个
            if isinstance(raw, list) and len(raw) > 0:
                return self._parse_response(raw[0], work_id)
            elif isinstance(raw, dict) and raw.get("workno"):
                return self._parse_response(raw, work_id)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.info(f"DLsite 作品 {work_id} 不存在 (404)")
            else:
                logger.warning(f"DLsite API 请求失败 {work_id}: HTTP {e.response.status_code}")
        except httpx.RequestError as e:
            logger.warning(f"DLsite API 网络错误 {work_id}: {e}")
        except Exception as e:
            logger.warning(f"DLsite API 解析错误 {work_id}: {e}")

        return None

    async def _fetch_product_legacy(self, work_id: str) -> dict[str, Any] | None:
        """备用 API：通过 DLsite 主站 JSON 接口获取"""
        num_part = re.sub(r'^(RJ|DL)', '', work_id)
        url = f"https://www.dlsite.com/maniax/product/info/ajax?productno={num_part}"

        try:
            async with httpx.AsyncClient(
                timeout=self._settings.dlsite_timeout,
                proxy=self._settings.dlsite_proxy or None,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://www.dlsite.com/",
                    "X-Requested-With": "XMLHttpRequest",
                },
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                raw = resp.json()

            # 备用 API 返回 {productno: {...}} 格式
            product_key = f"RJ{num_part}" if work_id.startswith("RJ") else f"DL{num_part}"
            if isinstance(raw, dict):
                product_data = raw.get(product_key) or raw.get(num_part)
                if product_data and isinstance(product_data, dict):
                    return self._parse_legacy_response(product_data, work_id)

        except Exception as e:
            logger.debug(f"DLsite 备用 API 也失败 {work_id}: {e}")

        return None

    def _parse_response(self, data: dict, work_id: str) -> dict[str, Any]:
        """解析主 API 响应，提取结构化信息"""
        result: dict[str, Any] = {
            "work_id": work_id,
            "title": None,
            "circle": None,
            "creator": None,
            "cv": None,
            "tags": [],
            "language": None,
            "description": None,
            "cover_url": None,
            "release_date": None,
            "source": "dlsite",
        }

        # 标题
        result["title"] = data.get("work_name") or data.get("work_name_en") or None

        # 社团
        result["circle"] = data.get("maker_name") or data.get("circle", {}).get("name") or None

        # 创作者（社团主/作者）
        creators = data.get("creators", {})
        if isinstance(creators, dict):
            # 尝试从不同角色中提取
            for role in ("writer", "illustrator", "scenario"):
                names = creators.get(role, [])
                if names:
                    result["creator"] = names[0] if isinstance(names[0], str) else names[0].get("name")
                    break
        elif isinstance(data.get("maker_name"), str):
            result["creator"] = data["maker_name"]

        # 声优
        if isinstance(creators, dict):
            voice_actors = creators.get("voice_actor") or creators.get("seiyuu") or []
            if voice_actors:
                cv_names = []
                for va in voice_actors:
                    if isinstance(va, str):
                        cv_names.append(va)
                    elif isinstance(va, dict):
                        cv_names.append(va.get("name", ""))
                result["cv"] = "、".join(filter(None, cv_names)) or None

        # 如果没有从 creators 中提取到，尝试其他字段
        if not result["cv"]:
            # 有些 API 响应把声优放在 tags 或其他字段
            for tag in data.get("tags", []):
                if isinstance(tag, dict) and tag.get("type") == "voice_actor":
                    result["cv"] = tag.get("name")
                    break

        # 标签
        tags = data.get("tags", [])
        if isinstance(tags, list):
            for tag in tags:
                if isinstance(tag, str):
                    result["tags"].append(tag)
                elif isinstance(tag, dict):
                    tag_name = tag.get("name") or tag.get("tag_name")
                    if tag_name:
                        result["tags"].append(tag_name)

        # 语言
        lang_names = data.get("language_labels") or data.get("work_lang") or []
        if isinstance(lang_names, list):
            for lang_name in lang_names:
                for key, val in _LANG_MAP.items():
                    if key in str(lang_name):
                        result["language"] = val
                        break
        elif isinstance(lang_names, str):
            for key, val in _LANG_MAP.items():
                if key in lang_names:
                    result["language"] = val

        # 描述
        result["description"] = data.get("work_outline") or data.get("outline") or None

        # 封面 URL
        image_url = data.get("image_main", {}).get("url") if isinstance(data.get("image_main"), dict) else None
        if not image_url:
            # 尝试从 thumbnail 字段获取
            thumbs = data.get("image_list") or data.get("thumbnails", [])
            if isinstance(thumbs, list) and thumbs:
                image_url = thumbs[0].get("url") if isinstance(thumbs[0], dict) else None
        if not image_url:
            # 构造标准封面 URL
            num_part = re.sub(r'^(RJ|DL)', '', work_id)
            padded = num_part.zfill(8)
            image_url = f"https://img.dlsite.jp/modpub/images2/work/doujin/RJ{padded[:6]}/RJ{padded}_img_main.jpg"
        result["cover_url"] = image_url

        # 发售日
        result["release_date"] = data.get("release_date") or data.get("regist_date") or None

        return result

    def _parse_legacy_response(self, data: dict, work_id: str) -> dict[str, Any]:
        """解析备用 API 响应"""
        result: dict[str, Any] = {
            "work_id": work_id,
            "title": None,
            "circle": None,
            "creator": None,
            "cv": None,
            "tags": [],
            "language": None,
            "description": None,
            "cover_url": None,
            "release_date": None,
            "source": "dlsite",
        }

        result["title"] = data.get("work_name")
        result["circle"] = data.get("maker_name")

        # 备用 API 的创作者信息较少，用社团名代替
        result["creator"] = data.get("maker_name")

        # 声优信息可能在 dl_id 或 genre 字段
        result["cv"] = None

        # 标签
        genre_list = data.get("genre") or []
        if isinstance(genre_list, list):
            result["tags"] = [str(g) for g in genre_list]

        result["description"] = data.get("work_outline")

        # 封面
        num_part = re.sub(r'^(RJ|DL)', '', work_id)
        padded = num_part.zfill(8)
        result["cover_url"] = f"https://img.dlsite.jp/modpub/images2/work/doujin/RJ{padded[:6]}/RJ{padded}_img_main.jpg"

        result["release_date"] = data.get("release_date")

        return result

    async def _rate_limit(self) -> None:
        """限流：确保请求间隔不低于设定值"""
        interval = 1.0 / max(self._settings.dlsite_rate_limit, 0.1)
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < interval:
            await asyncio.sleep(interval - elapsed)
        self._last_request_time = time.time()

    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()
