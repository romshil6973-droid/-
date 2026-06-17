"""Тесты модуля config.py — WorkdayMonitor v2.0."""
import os, sys, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from unittest.mock import patch
from core.config import validate_login, save_config, load_config, config_exists, get_pending_dir, SERVER_URL, API_TOKEN

class TestValidateLogin:
    def test_valid(self): assert validate_login("shilov") == (True, "")
    def test_digits(self): assert validate_login("user123")[0] is True
    def test_underscore(self): assert validate_login("ivan_p")[0] is True
    def test_empty(self): assert validate_login("")[0] is False
    def test_cyrillic(self): assert validate_login("Шилов")[0] is False
    def test_space(self): assert validate_login("shi lov")[0] is False
    def test_too_short(self): assert validate_login("ab")[0] is False
    def test_too_long(self): assert validate_login("a"*21)[0] is False
    def test_uppercase(self): assert validate_login("Shilov")[0] is False
    def test_min_len(self): assert validate_login("abc")[0] is True
    def test_max_len(self): assert validate_login("a"*20)[0] is True

class TestConfigIO:
    def test_save_load(self, tmp_path):
        p = tmp_path / "config.ini"
        with patch("core.config.get_config_path", return_value=p):
            save_config("shilov")
            r = load_config()
        assert r["login"] == "shilov"
        assert r["server_url"] == SERVER_URL
        assert r["api_token"] == API_TOKEN

    def test_load_missing(self, tmp_path):
        p = tmp_path / "none.ini"
        with patch("core.config.get_config_path", return_value=p):
            r = load_config()
        assert r["login"] == ""
        assert r["server_url"] == SERVER_URL

    def test_exists_true(self, tmp_path):
        p = tmp_path / "c.ini"
        with patch("core.config.get_config_path", return_value=p):
            save_config("shilov")
            assert config_exists() is True

    def test_exists_false_no_file(self, tmp_path):
        p = tmp_path / "none.ini"
        with patch("core.config.get_config_path", return_value=p):
            assert config_exists() is False

def test_pending_dir(tmp_path):
    with patch.dict(os.environ, {"LOCALAPPDATA": str(tmp_path)}):
        d = get_pending_dir()
    assert d.exists() and d.is_dir()
