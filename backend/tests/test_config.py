import json

from app import config


def test_runtime_settings_override_environment_and_persist(tmp_path, monkeypatch):
    settings_file = tmp_path / "runtime_settings.json"
    monkeypatch.setattr(config, "RUNTIME_SETTINGS_FILE", settings_file)
    monkeypatch.setenv("DLSITE_ENABLED", "true")
    config.get_settings.cache_clear()

    config.save_runtime_settings({"dlsite_enabled": False, "ai_model": "test-model"})
    settings = config.reload_settings()

    assert settings.dlsite_enabled is False
    assert settings.ai_model == "test-model"
    assert json.loads(settings_file.read_text(encoding="utf-8")) == {
        "ai_model": "test-model",
        "dlsite_enabled": False,
    }

    config.get_settings.cache_clear()
