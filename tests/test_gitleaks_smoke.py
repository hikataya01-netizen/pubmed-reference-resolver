"""tests/test_gitleaks_smoke.py — gitleaks secret 検出能力の回帰 guard (Day30)。

Day29 で導入した gitleaks pre-commit hook が、将来の rule database 変更で
secret を検出しなくなる回帰を pytest で検知する。`pre-commit run gitleaks`
を subprocess 実行し、ダミー slack token の検出と通常ファイルの pass を
検証する。

実装上の注意 (gitleaks pre-commit hook の挙動):
gitleaks の pre-commit hook entry は ``gitleaks git --pre-commit --staged``
かつ ``pass_filenames: false`` であり、コマンドラインで渡したパス
(``--files X``) は無視され、**git の staged 内容のみ** を scan する。
このため一時ファイルを単にディスクへ置いただけでは scan されず、
``git add`` で stage してから hook を実行する必要がある。

設計:
- pre-commit は cwd=repo root を前提とするため、一時ファイルは repo 内
  .gitleaks_smoke_tmp/ に置く (.gitignore で除外)。
- 一時ファイルは ``git add -f`` で stage し、hook 実行後に必ず unstage
  + ディレクトリ削除する (fixture の finally で index 汚染を防止)。
- ダミー token はリテラルで書くと test ファイル自身が gitleaks に
  ブロックされるため、実行時に文字列連結で組み立てる。token の suffix は
  rule の entropy 閾値 (entropy>=3) を満たすよう混在文字列にする
  (全て同一文字だと entropy 0 で検出されない)。
"""
from __future__ import annotations

import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
_SMOKE_DIR = REPO_ROOT / ".gitleaks_smoke_tmp"

# uv が無い環境では skip (CI / 開発機ともに uv は存在する想定だが安全側)
_HAS_UV = shutil.which("uv") is not None
_SKIP_REASON = "uv not available; cannot run pre-commit gitleaks"


def _unstage_smoke_dir() -> None:
    """smoke 一時ディレクトリ配下を index から確実に外す (失敗は無視)。"""
    subprocess.run(
        ["git", "rm", "-r", "--cached", "--force", "--quiet", str(_SMOKE_DIR)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def smoke_dir() -> Iterator[Path]:
    """repo 内の一時ディレクトリを生成し、test 後に unstage + 削除する。

    hook が staged 内容を scan する都合上、test 中に ``git add`` した
    一時ファイルが index に残ると repo を汚すため、finally で必ず index
    から外し、ディレクトリ自体も削除する。

    注: 固定パス ``.gitleaks_smoke_tmp/`` と共有 git index を使うため、
    本 test 群は **逐次実行を前提** とする (pytest-xdist 等での並列実行は
    未対応。並列化する場合は worker 別ディレクトリ化が必要)。
    """
    _SMOKE_DIR.mkdir(exist_ok=True)
    try:
        yield _SMOKE_DIR
    finally:
        _unstage_smoke_dir()
        shutil.rmtree(_SMOKE_DIR, ignore_errors=True)


def _stage_and_run_gitleaks(path: Path) -> subprocess.CompletedProcess[str]:
    """指定ファイルを stage し、pre-commit の gitleaks hook を実行する。

    gitleaks hook は staged 内容のみを scan するため、``git add -f`` で
    stage してから hook を起動する (``-f`` は .gitignore 除外下でも stage
    するため)。``--files`` は gitleaks hook が ``pass_filenames: false`` の
    ため実際の scan 対象には影響しない (staged 内容が scan される)。
    pre-commit の実行単位を明示する慣習的指定として残している。
    """
    subprocess.run(
        ["git", "add", "-f", str(path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return subprocess.run(
        ["uv", "run", "pre-commit", "run", "gitleaks", "--files", str(path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


@pytest.mark.skipif(not _HAS_UV, reason=_SKIP_REASON)
def test_gitleaks_detects_slack_bot_token(smoke_dir: Path) -> None:
    """ダミー slack bot token を含むファイルが gitleaks で detect される。

    回帰 guard: gitleaks の rule が slack-bot-token を検出しなくなったら FAIL。
    token はリテラルで書くとこの test ファイル自身が gitleaks scan で
    ブロックされるため、実行時に文字列連結で組み立てる。suffix は entropy
    閾値を満たすよう混在文字列にする。
    """
    suffix = "abc123XYZ789def456ghi012j"  # 混在文字列で entropy>=3 を満たす
    token = "xoxb" + "-" + "2222222222" + "-" + "1111111111111" + "-" + suffix
    leak_file = smoke_dir / "leak.txt"
    leak_file.write_text(f"slack_token = {token}\n", encoding="utf-8")

    result = _stage_and_run_gitleaks(leak_file)

    assert result.returncode != 0, (
        "expected gitleaks to DETECT the slack token (returncode != 0), "
        "but got returncode 0. gitleaks の rule database が変更された可能性が"
        "あります (現在 .pre-commit-config.yaml の rev は v8.30.1)。slack-bot-token "
        "rule がまだ存在し entropy 閾値が変わっていないか確認してください。\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


@pytest.mark.skipif(not _HAS_UV, reason=_SKIP_REASON)
def test_gitleaks_passes_clean_file(smoke_dir: Path) -> None:
    """機密を含まない通常ファイルは gitleaks を pass する (false positive guard)。"""
    clean_file = smoke_dir / "clean.txt"
    clean_file.write_text(
        "This is a normal reference list.\nSmith J, Brown K. Title. Journal 2024.\n",
        encoding="utf-8",
    )

    result = _stage_and_run_gitleaks(clean_file)

    assert result.returncode == 0, (
        "expected gitleaks to PASS the clean file (returncode 0), "
        f"but got returncode {result.returncode}.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
