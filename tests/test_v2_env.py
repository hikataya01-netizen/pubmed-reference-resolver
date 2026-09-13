"""audit.py が ~/.pubmed-reference-resolver.env の NCBI_API_KEY を使うこと (Day31)。"""

from __future__ import annotations

import pytest

import audit
from tests.v2_replay import FIX, replay_patches


@pytest.fixture
def home_with_key(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    (home / ".pubmed-reference-resolver.env").write_text("NCBI_API_KEY=ncbi-test-abc123\n", encoding="utf-8")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("NCBI_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)
    return home


def _run_capturing(tmp_path, monkeypatch, *extra: str) -> dict:
    captured: dict = {}
    for obj, attr, val in replay_patches(captured):
        monkeypatch.setattr(obj, attr, val)
    rc = audit.main(["--structured", str(FIX / "refs.json"), "-o", str(tmp_path / "out"),
                     "--no-docx", "--offline", *extra])
    assert rc == 0
    return captured


def test_ncbi_key_is_loaded_from_home_env_file(tmp_path, monkeypatch, home_with_key):
    captured = _run_capturing(tmp_path, monkeypatch)
    assert captured["api_key"] == "ncbi-test-abc123"


def test_no_env_file_flag_skips_loading(tmp_path, monkeypatch, home_with_key):
    captured = _run_capturing(tmp_path, monkeypatch, "--no-env-file")
    assert captured["api_key"] is None


def test_explicit_api_key_wins_over_env_file(tmp_path, monkeypatch, home_with_key):
    captured = _run_capturing(tmp_path, monkeypatch, "--api-key", "cli-key-999")
    assert captured["api_key"] == "cli-key-999"
