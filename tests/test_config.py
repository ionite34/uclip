import pytest


# Fixture return a patched config module
@pytest.fixture(scope="function")
def patched_config(monkeypatch, mem_keyring):
    from uclip import config

    monkeypatch.setattr(config, "keyring", mem_keyring)
    return config


def test_load(patched_config):
    cfg = patched_config.Config()
    assert len(cfg) == 0
    cfg["test_key"] = "test_value"
    cfg.save()
    assert len(cfg) == 1
    assert cfg.load() is True
    assert cfg["test_key"] == "test_value"


def test_save(patched_config):
    cfg = patched_config.Config()
    assert len(cfg) == 0
    cfg["test_key"] = "test_value"
    cfg.save()
    assert cfg.load() is True
    assert cfg["test_key"] == "test_value"


def test_valid(patched_config):
    cfg = patched_config.Config()
    assert cfg.valid is False
