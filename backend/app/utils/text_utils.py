import re
import unicodedata


def detect_language(text: str) -> str:
    """检测文本主要语言"""
    if not text:
        return "other"

    ja_chars = 0
    zh_chars = 0
    en_chars = 0

    for char in text:
        cp = ord(char)
        # Japanese: Hiragana, Katakana, CJK (shared with Chinese)
        if 0x3040 <= cp <= 0x309F or 0x30A0 <= cp <= 0x30FF:
            ja_chars += 1
        # CJK Unified Ideographs (shared, but weighted toward Chinese)
        elif 0x4E00 <= cp <= 0x9FFF:
            zh_chars += 1
        # ASCII letters
        elif 0x41 <= cp <= 0x5A or 0x61 <= cp <= 0x7A:
            en_chars += 1

    # If has Hiragana/Katakana, likely Japanese
    if ja_chars > 0:
        return "ja"
    if zh_chars > en_chars:
        return "zh"
    if en_chars > zh_chars:
        return "en"
    return "other"


def clean_title(title: str) -> str:
    """清理标题文本"""
    # Remove common suffixes/prefixes
    title = re.sub(r'\[.*?\]', '', title)  # Remove brackets content
    title = re.sub(r'\(.*?\)', '', title)  # Remove parentheses content
    title = re.sub(r'【.*?】', '', title)  # Remove Japanese brackets
    title = re.sub(r'\s+', ' ', title).strip()
    return title
