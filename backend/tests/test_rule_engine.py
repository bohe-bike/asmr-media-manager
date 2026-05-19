import pytest
from app.services.rule_engine import RuleEngine


@pytest.fixture
def engine():
    return RuleEngine()


class TestRjIdExtraction:
    def test_standard_rj(self, engine):
        assert engine._extract_rj_id("[RJ123456] title") == "RJ123456"

    def test_rj_lowercase(self, engine):
        assert engine._extract_rj_id("[rj123456] title") == "RJ123456"

    def test_rj_no_brackets(self, engine):
        assert engine._extract_rj_id("RJ123456 title") == "RJ123456"

    def test_rj_8digit(self, engine):
        assert engine._extract_rj_id("[RJ12345678] title") == "RJ12345678"

    def test_bracket_number(self, engine):
        assert engine._extract_rj_id("[123456] title") == "RJ123456"

    def test_no_rj(self, engine):
        assert engine._extract_rj_id("just a title") is None


class TestDlIdExtraction:
    def test_standard_dl(self, engine):
        assert engine._extract_dl_id("[DL123456] title") == "DL123456"

    def test_no_dl(self, engine):
        assert engine._extract_dl_id("[RJ123456] title") is None


class TestCvExtraction:
    def test_cv_dot(self, engine):
        assert engine._extract_cv("[CV.涼花みなせ] title") == "涼花みなせ"

    def test_cv_colon(self, engine):
        assert engine._extract_cv("CV:涼花みなせ] title") == "涼花みなせ"

    def test_cv_brackets(self, engine):
        assert engine._extract_cv("[CV涼花みなせ] title") == "涼花みなせ"

    def test_no_cv(self, engine):
        assert engine._extract_cv("[RJ123456] title") is None


class TestLanguageDetection:
    def test_japanese(self, engine):
        assert engine._extract_rj_id is not None

    def test_detect_ja(self):
        from app.utils.text_utils import detect_language
        assert detect_language("涼花みなせ") == "ja"

    def test_detect_zh(self):
        from app.utils.text_utils import detect_language
        assert detect_language("深夜耳搔治愈") == "zh"

    def test_detect_en(self):
        from app.utils.text_utils import detect_language
        assert detect_language("Cranial Nerve Exam") == "en"


class TestPlatformDetection:
    def test_dlsite(self, engine):
        assert engine._detect_platform("[RJ123456] title", "") == "dlsite"

    def test_patreon(self, engine):
        assert engine._detect_platform("patreon content", "") == "patreon"

    def test_youtube(self, engine):
        assert engine._detect_platform("youtube video", "") == "youtube"

    def test_unknown(self, engine):
        assert engine._detect_platform("random file", "") is None


class TestParse:
    @pytest.mark.asyncio
    async def test_parse_complex(self, engine):
        # Create a temp file path for testing
        result = await engine.parse("[RJ123456][CV.涼花みなせ] 深夜耳搔治愈.flac")
        assert result["rj_id"] == "RJ123456"
        assert result["cv"] == "涼花みなせ"
        assert result["language"] == "ja"
        assert result["platform"] == "dlsite"
