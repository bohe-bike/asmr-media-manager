import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class PlexService:
    """Plex Server API 服务：触发媒体库刷新"""

    def __init__(self):
        self._settings = get_settings()

    @property
    def enabled(self) -> bool:
        return bool(self._settings.plex_url and self._settings.plex_token)

    async def refresh_library(self, section_id: int | None = None) -> bool:
        """通知 Plex 刷新媒体库。

        section_id: 指定库 ID，None 则刷新所有库
        返回 True 表示成功发送通知。
        """
        if not self.enabled:
            logger.debug("Plex not configured, skipping refresh notification")
            return False

        base_url = self._settings.plex_url.rstrip("/")
        token = self._settings.plex_token

        try:
            if section_id:
                url = f"{base_url}/library/sections/{section_id}/refresh"
            else:
                # 刷新所有库
                url = f"{base_url}/library/sections/all/refresh"

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, params={"X-Plex-Token": token})
                resp.raise_for_status()

            logger.info(f"Plex library refresh triggered (section={section_id or 'all'})")
            return True
        except httpx.RequestError as e:
            logger.warning(f"Failed to trigger Plex refresh: {e}")
            return False
        except httpx.HTTPStatusError as e:
            logger.warning(f"Plex refresh failed: HTTP {e.response.status_code}")
            return False

    async def get_sections(self) -> list[dict]:
        """获取 Plex 所有媒体库列表。"""
        if not self.enabled:
            return []

        base_url = self._settings.plex_url.rstrip("/")
        token = self._settings.plex_token

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{base_url}/library/sections",
                    params={"X-Plex-Token": token},
                    headers={"Accept": "application/json"},
                )
                resp.raise_for_status()
                data = resp.json()

            sections = []
            for dir in data.get("MediaContainer", {}).get("Directory", []):
                sections.append({
                    "id": dir.get("key"),
                    "title": dir.get("title"),
                    "type": dir.get("type"),
                    "scanner": dir.get("scanner"),
                    "agent": dir.get("agent"),
                    "language": dir.get("language"),
                })
            return sections
        except Exception as e:
            logger.warning(f"Failed to get Plex sections: {e}")
            return []

    async def test_connection(self) -> dict:
        """测试 Plex 连接，返回服务器信息。"""
        if not self.enabled:
            return {"connected": False, "error": "Plex 未配置"}

        base_url = self._settings.plex_url.rstrip("/")
        token = self._settings.plex_token

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{base_url}/",
                    params={"X-Plex-Token": token},
                    headers={"Accept": "application/json"},
                )
                resp.raise_for_status()
                data = resp.json()

            server = data.get("MediaContainer", {})
            return {
                "connected": True,
                "name": server.get("friendlyName", "Unknown"),
                "version": server.get("version", "Unknown"),
                "platform": server.get("platform", "Unknown"),
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}
