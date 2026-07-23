from app.models.author_rule import AuthorRule
from app.services.author_matcher import AuthorMatcher


def test_get_target_texts_limits_rule_to_configured_target():
    rule = AuthorRule(keyword="creator", match_target="directory")
    texts = {
        "filename": "creator - track.mp3",
        "directory": "album",
        "metadata_artist": "creator",
    }

    assert AuthorMatcher.get_target_texts(rule, texts) == [("directory", "album")]


def test_get_target_texts_returns_every_field_for_all_target():
    rule = AuthorRule(keyword="creator", match_target="all")
    texts = {"filename": "track.mp3", "directory": "creator"}

    assert AuthorMatcher.get_target_texts(rule, texts) == list(texts.items())
