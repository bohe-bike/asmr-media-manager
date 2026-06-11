import os
import re

from app.utils.text_utils import detect_language, clean_title


class RuleEngine:
    """文件名解析引擎：从文件名/目录名中提取结构化元数据"""

    # ── RJ/DL 号 ──────────────────────────────────────────────
    RJ_PATTERN = re.compile(r'RJ(\d{6,8})', re.IGNORECASE)
    DL_PATTERN = re.compile(r'DL(\d{6,8})', re.IGNORECASE)
    # 方括号包裹的纯数字（6-8位）
    BRACKET_NUM_PATTERN = re.compile(r'\[(\d{6,8})\]')
    # 无前缀的裸数字（行首或独立出现，6-8位）
    STANDALONE_NUM_PATTERN = re.compile(r'(?:^|[\s_\-])(\d{6,8})(?:[\s_\-\.]|$)')

    # ── CV（声优）─────────────────────────────────────────────
    CV_PATTERNS = [
        # CV.xxx] 或 CV.xxx）
        re.compile(r'CV[\.．:：]\s*(.+?)[\]\)）】]', re.IGNORECASE),
        # [CV.xxx] 或 [CV：xxx]
        re.compile(r'\[CV[\.．:：]?\s*(.+?)\]', re.IGNORECASE),
        # 【CV：xxx】（全角方括号+中文冒号）
        re.compile(r'【\s*CV[\.．:：]?\s*(.+?)】', re.IGNORECASE),
        # (CV xxx) 或 （CV xxx）
        re.compile(r'[（(]\s*CV[\.．:：]?\s*(.+?)[）)]', re.IGNORECASE),
        # CV_xxx（下划线分隔）
        re.compile(r'CV[_]\s*(.+?)(?:[\s_\-\.]|$)', re.IGNORECASE),
        # CV xxx（空格分隔，无括号，到行尾或分隔符为止）
        re.compile(r'(?<![a-zA-Z])CV[\.．:：\s]\s*(.+?)(?:\s*[\[（(]|$)', re.IGNORECASE),
    ]
    # 多 CV 分隔符
    CV_SEPARATORS = re.compile(r'[×✕✖/／、&＆]')

    BRACKET_CONTENT = re.compile(r'\[(.+?)\]')

    # ── 常见噪音标签（标题清理用）────────────────────────────────
    NOISE_TAGS = [
        '24bit', 'FLAC', 'MP3', 'AAC', '320K', '128K', '192K', 'V0', 'V2',
        'Hi-Res', 'HiRes', 'LOSSLESS', 'WEB', 'WEB-DL', 'Blu-ray',
        'dmhy', 'SUB', 'ANON', 'LFN', 'VCB', 'RH', 'ANK',
        'RARBG', 'YTS', 'ETRG', 'PROPER', 'REPACK',
    ]
    NOISE_TAG_PATTERN = re.compile(
        r'\[(' + '|'.join(re.escape(t) for t in NOISE_TAGS) + r')\]',
        re.IGNORECASE,
    )

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

        # 从文件名和父目录名中提取（合并搜索）
        search_texts = [name_without_ext, dirname]

        # Extract RJ/DL ID
        result["rj_id"] = self._extract_rj_id(search_texts)
        result["dl_id"] = self._extract_dl_id(search_texts)

        # Extract CV
        result["cv"] = self._extract_cv(name_without_ext)

        # Extract title
        result["title"] = self._extract_title(name_without_ext, result)

        # Detect language
        result["language"] = detect_language(name_without_ext)

        # Detect platform
        result["platform"] = self._detect_platform(name_without_ext, dirname)

        return result

    def parse_with_ancestors(self, file_path: str, max_depth: int = 2) -> dict:
        """解析文件路径，递归向上查找目录名中的 RJ号。

        max_depth: 向上查找的目录层级数（默认2，即父目录和祖父目录）
        """
        filename = os.path.basename(file_path)
        name_without_ext = os.path.splitext(filename)[0]

        # 收集所有可搜索的文本
        search_texts = [name_without_ext]
        current_dir = os.path.dirname(file_path)
        for _ in range(max_depth):
            dir_name = os.path.basename(current_dir)
            if dir_name:
                search_texts.append(dir_name)
            parent = os.path.dirname(current_dir)
            if parent == current_dir:
                break
            current_dir = parent

        result = {
            "rj_id": None,
            "dl_id": None,
            "cv": None,
            "title": None,
            "circle": None,
            "language": None,
            "platform": None,
        }

        # Extract RJ/DL ID（从所有层级中搜索）
        result["rj_id"] = self._extract_rj_id(search_texts)
        result["dl_id"] = self._extract_dl_id(search_texts)

        # Extract CV（仅从文件名中提取）
        result["cv"] = self._extract_cv(name_without_ext)

        # Extract title
        result["title"] = self._extract_title(name_without_ext, result)

        # Detect language
        result["language"] = detect_language(name_without_ext)

        # Detect platform
        dirname = os.path.basename(os.path.dirname(file_path))
        result["platform"] = self._detect_platform(name_without_ext, dirname)

        return result

    def _extract_rj_id(self, texts: str | list[str]) -> str | None:
        """从文本中提取 RJ号，支持多个搜索文本"""
        if isinstance(texts, str):
            texts = [texts]

        for text in texts:
            if not text:
                continue
            # 优先：RJ + 数字
            match = self.RJ_PATTERN.search(text)
            if match:
                return f"RJ{match.group(1)}"
            # 次优先：方括号包裹的数字
            match = self.BRACKET_NUM_PATTERN.search(text)
            if match:
                num = match.group(1)
                if len(num) >= 6:
                    return f"RJ{num}"
            # 最后：裸数字（仅当文件名/目录名看起来像作品号时）
            match = self.STANDALONE_NUM_PATTERN.search(text)
            if match:
                num = match.group(1)
                if len(num) >= 6:
                    return f"RJ{num}"
        return None

    def _extract_dl_id(self, texts: str | list[str]) -> str | None:
        if isinstance(texts, str):
            texts = [texts]
        for text in texts:
            if not text:
                continue
            match = self.DL_PATTERN.search(text)
            if match:
                return f"DL{match.group(1)}"
        return None

    def _extract_cv(self, text: str) -> str | None:
        for pattern in self.CV_PATTERNS:
            match = pattern.search(text)
            if match:
                raw = match.group(1).strip()
                # 处理多 CV 的情况
                parts = self.CV_SEPARATORS.split(raw)
                cv_list = [p.strip() for p in parts if p.strip()]
                if cv_list:
                    return "、".join(cv_list)
        return None

    def _extract_title(self, filename: str, extracted: dict) -> str:
        """从文件名中提取标题（减法式）"""
        title = filename
        # Remove RJ/DL IDs
        if extracted.get("rj_id"):
            title = title.replace(extracted["rj_id"], "")
            title = re.sub(r'\[?\d{6,8}\]?', '', title)
        if extracted.get("dl_id"):
            title = title.replace(extracted["dl_id"], "")
        # Remove CV markers（所有模式）
        for pattern in self.CV_PATTERNS:
            title = pattern.sub('', title)
        # Remove noise tags
        title = self.NOISE_TAG_PATTERN.sub('', title)
        # Remove common technical tags not in blacklist
        title = re.sub(r'\[24bit\]', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\[FLAC\]', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\[MP3\]', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\[Hi-Res\]', '', title, flags=re.IGNORECASE)
        # Clean remaining brackets but keep content
        title = re.sub(r'\[([^\]]+)\]', r'\1', title)
        # Remove leading/trailing brackets and their content if leftover
        title = re.sub(r'^[\s\-_]+', '', title)
        title = re.sub(r'[\s\-_]+$', '', title)
        # Normalize whitespace
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
