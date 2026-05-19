import os
import re

from app.utils.text_utils import detect_language, clean_title


class RuleEngine:
    """文件名解析引擎：从文件名/目录名中提取结构化元数据"""

    RJ_PATTERN = re.compile(r'RJ(\d{6,8})', re.IGNORECASE)
    DL_PATTERN = re.compile(r'DL(\d{6,8})', re.IGNORECASE)
    BRACKET_NUM_PATTERN = re.compile(r'\[(\d{6,8})\]')
    CV_PATTERNS = [
        re.compile(r'CV[\.．:：]\s*(.+?)[\]\)】]', re.IGNORECASE),
        re.compile(r'\[CV[\.．]?\s*(.+?)\]', re.IGNORECASE),
    ]
    BRACKET_CONTENT = re.compile(r'\[(.+?)\]')

    async def parse(self, file_path: str) -> dict:
        """解析文件路径，返回结构化元数据"""
        filename = os.path.basename(file_path)
        dirname = os.path.basename(os.path.dirname(file_path))
        name_without_ext = os.path.splitext(filename)[0]

        result = {
            "rj_id": None,
            "dl_id": None,
            "cv": None,
            "title": None,
            "circle": None,
            "language": None,
            "platform": None,
        }

        # Extract RJ/DL ID
        result["rj_id"] = self._extract_rj_id(name_without_ext)
        result["dl_id"] = self._extract_dl_id(name_without_ext)

        # Extract CV
        result["cv"] = self._extract_cv(name_without_ext)

        # Extract title
        result["title"] = self._extract_title(name_without_ext, result)

        # Detect language
        result["language"] = detect_language(name_without_ext)

        # Detect platform
        result["platform"] = self._detect_platform(name_without_ext, dirname)

        return result

    def _extract_rj_id(self, text: str) -> str | None:
        match = self.RJ_PATTERN.search(text)
        if match:
            return f"RJ{match.group(1)}"
        match = self.BRACKET_NUM_PATTERN.search(text)
        if match:
            num = match.group(1)
            if len(num) >= 6:
                return f"RJ{num}"
        return None

    def _extract_dl_id(self, text: str) -> str | None:
        match = self.DL_PATTERN.search(text)
        if match:
            return f"DL{match.group(1)}"
        return None

    def _extract_cv(self, text: str) -> str | None:
        for pattern in self.CV_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
        return None

    def _extract_title(self, filename: str, extracted: dict) -> str:
        """从文件名中提取标题"""
        title = filename
        # Remove RJ/DL IDs
        if extracted.get("rj_id"):
            title = title.replace(extracted["rj_id"], "")
            title = re.sub(r'\[?\d{6,8}\]?', '', title)
        if extracted.get("dl_id"):
            title = title.replace(extracted["dl_id"], "")
        # Remove CV markers
        title = re.sub(r'CV[\.．:：]\s*.+?[\]\)】]', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\[CV[\.．]?\s*.+?\]', '', title, flags=re.IGNORECASE)
        # Remove common tags
        title = re.sub(r'\[24bit\]', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\[FLAC\]', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\[MP3\]', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\[Hi-Res\]', '', title, flags=re.IGNORECASE)
        # Clean up brackets but keep content
        title = re.sub(r'\[([^\]]+)\]', r'\1', title)
        # Clean
        title = re.sub(r'\s+', ' ', title).strip()
        title = title.strip('- _')
        return title if title else filename

    def _detect_platform(self, filename: str, dirname: str) -> str | None:
        combined = f"{filename} {dirname}".lower()
        if "rj" in combined or "dl" in combined or "dlsite" in combined:
            return "dlsite"
        if "patreon" in combined:
            return "patreon"
        if "youtube" in combined or "yt" in combined:
            return "youtube"
        return None
