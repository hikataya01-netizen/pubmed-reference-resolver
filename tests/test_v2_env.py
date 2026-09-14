"""audit.py が ~/.pubmed-reference-resolver.env の NCBI_API_KEY を使うこと (Day31)。"""

from __future__ import annotations

from pathlib import Path

import pytest

import audit
from tests.v2_replay import FIX, replay_patches

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def home_with_key(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    (home / ".pubmed-reference-resolver.env").write_text("NCBI_API_KEY=ncbi-test-abc123\n", encoding="utf-8")
    monkeypatch.setenv("HOME", str(home))
    # delenv だと元々未設定の場合に何も記録されず、他テストが残した setenv 値の
    # リセット漏れを検出できない。空値でセットし直し、_inject_env_kv の
    # 「空値は未設定とみなす」契約で確実に上書き可能な状態にする。
    monkeypatch.setenv("NCBI_API_KEY", "")
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
    if (REPO / ".env").exists():
        pytest.skip("repo-root .env present; loader candidate 1 would take precedence")
    captured = _run_capturing(tmp_path, monkeypatch)
    assert captured["api_key"] == "ncbi-test-abc123"


def test_no_env_file_flag_skips_loading(tmp_path, monkeypatch, home_with_key):
    if (REPO / ".env").exists():
        pytest.skip("repo-root .env present; loader candidate 1 would take precedence")
    captured = _run_capturing(tmp_path, monkeypatch, "--no-env-file")
    assert captured["api_key"] is None


def test_explicit_api_key_wins_over_env_file(tmp_path, monkeypatch, home_with_key):
    captured = _run_capturing(tmp_path, monkeypatch, "--api-key", "cli-key-999")
    assert captured["api_key"] == "cli-key-999"


def test_non_empty_env_var_wins_over_env_file(tmp_path, monkeypatch, home_with_key):
    monkeypatch.setenv("NCBI_API_KEY", "from-env-777")
    captured = _run_capturing(tmp_path, monkeypatch)
    assert captured["api_key"] == "from-env-777"
