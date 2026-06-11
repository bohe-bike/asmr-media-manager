import re
import unicodedata

# 联系方式/社交账号的匹配模式（应被过滤）
CONTACT_PATTERNS = re.compile(
    r'(?:TG[@:]|TG群|微信[::]|WeChat[::]|QQ[:\s]|QQ群|'
    r't\.me/|twitter\.com/|pixiv\.net/|bilibili\.com/|'
    r'@[a-zA-Z0-9_]{3,}|'  # @username（至少3位）
    r'https?://)',  # URL
    re.IGNORECASE,
)

# 创作者字段的分隔符
_ARTIST_SEPARATORS = re.compile(r'[;；、/&＆×✕]|(?:\s+feat\.?\s+)|(?:\s+ft\.?\s+)', re.IGNORECASE)


def split_artist(raw: str) -> str:
    """从原始创作者字段中提取主创作者。

    规则：
    1. 按常见分隔符拆分（;、/、&、feat. 等）
    2. 过滤掉联系方式/社交账号（TG@、微信:、QQ:、URL 等）
    3. 取第一个有效名字作为主创作者
    """
    if not raw or not raw.strip():
        return raw

    parts = _ARTIST_SEPARATORS.split(raw)
    for part in parts:
        name = part.strip()
        if not name:
            continue
        # 跳过联系方式
        if CONTACT_PATTERNS.search(name):
            continue
        # 跳过纯数字或过短的字符串
        if len(name) < 2 or name.isdigit():
            continue
        return name

    # 全部被过滤了，返回原始字符串（降级处理）
    return raw.strip()


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
