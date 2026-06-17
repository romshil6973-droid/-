"""Тесты модуля uploader.py — WorkdayMonitor v2.0."""
import os, sys, pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.uploader import upload_report, retry_pending_uploads, check_server, pending_count

CFG = {'login': 'testuser', 'server_url': 'https://46.149.68.148', 'api_token': 'SP2026secure'}

def mkfile(tmp_path, name="report.xlsx"):
    p = tmp_path / name; p.write_bytes(b"PK fake"); return str(p)

class TestCheckServer:
    def test_ok(self):
        r = MagicMock(); r.status_code = 200
        with patch("core.uploader.requests.get", return_value=r), patch("core.uploader.load_config", return_value=CFG):
            assert check_server() is True
    def test_fail_500(self):
        r = MagicMock(); r.status_code = 500
        with patch("core.uploader.requests.get", return_value=r), patch("core.uploader.load_config", return_value=CFG):
            assert check_server() is False
    def test_connection_error(self):
        import requests as req
        with patch("core.uploader.requests.get", side_effect=req.ConnectionError()), patch("core.uploader.load_config", return_value=CFG):
            assert check_server() is False

class TestUploadReport:
    def test_success(self, tmp_path):
        f = mkfile(tmp_path); r = MagicMock(); r.status_code = 200
        with patch("core.uploader.requests.post", return_value=r), patch("core.uploader.load_config", return_value=CFG), patch("core.uploader.get_pending_dir", return_value=tmp_path/"p"):
            assert upload_report(f, "testuser") is True
    def test_no_server(self, tmp_path):
        f = mkfile(tmp_path); p = tmp_path/"p"; p.mkdir()
        import requests as req
        with patch("core.uploader.requests.post", side_effect=req.ConnectionError()), patch("core.uploader.load_config", return_value=CFG), patch("core.uploader.get_pending_dir", return_value=p):
            assert upload_report(f, "testuser") is False
        assert (p/"report.xlsx").exists()
    def test_401(self, tmp_path):
        f = mkfile(tmp_path); p = tmp_path/"p"; p.mkdir(); r = MagicMock(); r.status_code = 401
        with patch("core.uploader.requests.post", return_value=r), patch("core.uploader.load_config", return_value=CFG), patch("core.uploader.get_pending_dir", return_value=p):
            assert upload_report(f, "testuser") is False

class TestRetryPending:
    def test_success(self, tmp_path):
        p = tmp_path/"p"; p.mkdir(); (p/"r.xlsx").write_bytes(b"x")
        r = MagicMock(); r.status_code = 200
        with patch("core.uploader.requests.post", return_value=r), patch("core.uploader.load_config", return_value=CFG), patch("core.uploader.get_pending_dir", return_value=p):
            assert retry_pending_uploads() == 1
    def test_no_login(self):
        with patch("core.uploader.load_config", return_value=dict(CFG, login="")):
            assert retry_pending_uploads() == 0

def test_pending_count(tmp_path):
    p = tmp_path/"p"; p.mkdir()
    (p/"a.xlsx").write_bytes(b"x"); (p/"b.xlsx").write_bytes(b"x")
    with patch("core.uploader.get_pending_dir", return_value=p):
        assert pending_count() == 2
