import json
import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class AIService:
    """调用线上 OpenAI 兼容 API 的 AI 服务"""

    def __init__(self):
        self._settings = get_settings()

    @property
    def enabled(self) -> bool:
        return self._settings.ai_enabled and bool(self._settings.ai_api_url)

    async def chat(self, messages: list[dict[str, str]], temperature: float = 0.7) -> str:
        """发送对话请求，返回文本回复"""
        if not self.enabled:
            raise RuntimeError("AI 服务未启用，请在设置中配置 API 地址和密钥")

        url = self._settings.ai_api_url.rstrip("/")
        if not url.endswith("/chat/completions"):
            url += "/chat/completions"

        headers = {"Content-Type": "application/json"}
        if self._settings.ai_api_key:
            headers["Authorization"] = f"Bearer {self._settings.ai_api_key}"

        payload = {
            "model": self._settings.ai_model,
            "messages": messages,
            "temperature": temperature,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def analyze_media_title(self, filename: str) -> dict[str, Any]:
        """用 AI 分析媒体文件名，提取结构化信息"""
        prompt = (
            "分析以下 ASMR 媒体文件名，提取结构化信息。"
            "返回 JSON 格式，字段包括：title(标题), cv(声优), circle(社团/社团), "
            "rj_id(DLsite 作品号), language(语言: ja/zh/en), tags(标签数组)。\n"
            f"文件名：{filename}"
        )

        try:
            result = await self.chat([
                {"role": "system", "content": "你是 ASMR 媒体信息分析助手，只返回 JSON，不要其他文字。"},
                {"role": "user", "content": prompt},
            ], temperature=0.1)

            # 尝试解析 JSON
            result = result.strip()
            if result.startswith("```"):
                result = result.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            return json.loads(result)
        except Exception as e:
            logger.warning(f"AI 分析文件名失败: {e}")
            return {}

    async def generate_description(self, title: str, cv: str = "", circle: str = "") -> str:
        """用 AI 生成媒体描述"""
        info_parts = [f"标题：{title}"]
        if cv:
            info_parts.append(f"声优：{cv}")
        if circle:
            info_parts.append(f"社团：{circle}")

        prompt = (
            f"为以下 ASMR 作品写一段简短的中文描述（50-100字）：\n"
            + "\n".join(info_parts)
        )

        try:
            return await self.chat([
                {"role": "system", "content": "你是 ASMR 内容描述助手，用简洁优美的中文描述。"},
                {"role": "user", "content": prompt},
            ], temperature=0.7)
        except Exception as e:
            logger.warning(f"AI 生成描述失败: {e}")
            return ""
