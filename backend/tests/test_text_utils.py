import pytest
from app.utils.text_utils import detect_language, clean_title


class TestDetectLanguage:
    def test_japanese_hiragana(self):
        assert detect_language("こんばんは") == "ja"

    def test_japanese_katakana(self):
        assert detect_language("カタカナ") == "ja"

    def test_chinese(self):
        assert detect_language("深夜耳搔治愈") == "zh"

    def test_english(self):
        assert detect_language("Hello World") == "en"

    def test_empty(self):
        assert detect_language("") == "other"

    def test_mixed_ja(self):
        # Has katakana, should be ja
        assert detect_language("涼花みなせASMR") == "ja"


class TestCleanTitle:
    def test_remove_brackets(self):
        assert clean_title("[tag] title") == "title"

    def test_remove_parentheses(self):
        assert clean_title("title (info)") == "title"

    def test_remove_japanese_brackets(self):
        assert clean_title("【info】title") == "title"

    def test_multiple_spaces(self):
        result = clean_title("title   with   spaces")
        assert "  " not in result
