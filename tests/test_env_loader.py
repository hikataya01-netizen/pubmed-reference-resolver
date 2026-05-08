"""Tests for main.py env loader (load_env_files / _parse_env_file).

Background:
    Day7/Phase ζ Stage 2 (2026/05/02) revealed that load_env_files() failed
    to inject .env values when the parent shell exported empty environment
    variables (e.g. ANTHROPIC_API_KEY=""). The Claude Code harness exhibits
    this behavior to prevent accidental key leakage to subprocesses.

    The current logic at main.py:91-92 reads:
        if k not in os.environ and v:
            os.environ[k] = v
    This skips overwriting whenever the key *exists* in os.environ, even if
    its value is an empty string. The fix: treat empty-string existing
    values as "unset for our purposes" and overwrite them.

    See docs/sessions/day7/PHASE_0_VERIFICATION_REPORT.md §8.8 (学び 7.6)
    and §9.1 for the full rationale.
"""

import os
from pathlib import Path

import pytest

import main as main_mod


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def env_file_in_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a .env file in tmp_path and chdir to it so load_env_files()
    picks it up via the cwd candidate."""
    p = tmp_path / ".env"
    p.write_text(
        "ANTHROPIC_API_KEY=sk-ant-test-12345\n"
        "NCBI_API_KEY=ncbi-test-67890\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    return p


# -----------------------------------------------------------------------------
# Tests for the regression fix (the new behavior)
# -----------------------------------------------------------------------------


def test_load_env_files_overwrites_empty_existing_env_var(
    env_file_in_cwd: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """When os.environ has an empty value, .env must overwrite it.

    This is the case observed in Day7 Stage 2: the Claude Code harness
    exports ANTHROPIC_API_KEY="" to subprocesses, which previously
    blocked the .env file value from taking effect.
    """
    # Pre-condition: empty existing env var (mimicking the harness)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    assert "ANTHROPIC_API_KEY" in os.environ
    assert os.environ["ANTHROPIC_API_KEY"] == ""

    # Action: load .env from cwd
    loaded = main_mod.load_env_files()

    # Assertion: env var should now hold the .env value
    assert os.environ["ANTHROPIC_API_KEY"] == "sk-ant-test-12345", (
        "Empty existing ANTHROPIC_API_KEY must be overwritten by .env value "
        "(Day7/Phase ζ §8.8 学び 7.6 fix)"
    )
    # Sanity: loaded list should mention the .env file
    assert any(".env" in s for s in loaded), (
        f"loaded list should mention the .env file, got: {loaded}"
    )


# -----------------------------------------------------------------------------
# Tests for behavior that must be preserved (regression guards)
# -----------------------------------------------------------------------------


def test_load_env_files_preserves_non_empty_existing_env_var(
    env_file_in_cwd: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """When os.environ has a non-empty user-provided value, .env must NOT
    overwrite it. Preserves the docstring contract: ユーザー指定が最優先.
    """
    # Pre-condition: user-provided non-empty value
    monkeypatch.setenv("ANTHROPIC_API_KEY", "user-provided-key-99999")

    # Action
    main_mod.load_env_files()

    # Assertion: user-provided value must survive
    assert os.environ["ANTHROPIC_API_KEY"] == "user-provided-key-99999", (
        "Non-empty user-provided ANTHROPIC_API_KEY must NOT be overwritten "
        "by .env (preserves ユーザー指定が最優先 contract)"
    )


def test_load_env_files_skips_empty_value_in_env_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """When .env contains KEY= (empty value), os.environ must not be set.

    Preserves the existing behavior of the `v` truthy check at main.py:91.
    """
    # Pre-condition: .env with empty value
    p = tmp_path / ".env"
    p.write_text("ANTHROPIC_API_KEY=\n", encoding="utf-8")

    # Ensure no pre-existing key in os.environ
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    # Action
    monkeypatch.chdir(tmp_path)
    main_mod.load_env_files()

    # Assertion: env var should remain unset
    assert "ANTHROPIC_API_KEY" not in os.environ, (
        "Empty .env value must not set os.environ "
        "(preserves the `v` truthy check)"
    )
