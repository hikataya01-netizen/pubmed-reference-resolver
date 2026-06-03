# Contributing to pubmed-reference-resolver

本プロジェクトへの contribution を歓迎する。本ドキュメントは開発環境の最小
セットアップと開発フローを記述する。

## 開発環境セットアップ

1. **uv install** (Python パッケージマネージャ):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   詳細: https://docs.astral.sh/uv/

2. **依存関係 install** (production + dev):
   ```bash
   uv sync --group dev
   ```

3. **pre-commit hook install** (機密データ commit 予防):
   ```bash
   uv run pre-commit install
   ```
   これで `.git/hooks/pre-commit` が配置され、`git commit` 時に gitleaks が
   自動実行される。

## 開発フロー

1. main branch から feature branch を切る:
   ```bash
   git checkout -b feat/your-feature
   ```

2. 機能変更 → test 追加 → 全 pytest PASS 確認:
   ```bash
   uv run pytest tests/ -v
   ```

3. commit (pre-commit hook が gitleaks scan を自動実行):
   ```bash
   git add <files>
   git commit -m "feat: your feature"
   ```

4. push → CI で再 scan + test 実行:
   ```bash
   git push origin feat/your-feature
   ```

5. CI green を確認してから PR open。

## Commit メッセージ規約

[Conventional Commits](https://www.conventionalcommits.org/) に準拠する:

| prefix | 用途 |
|:---|:---|
| `feat:` | 新機能 |
| `fix:` | バグ修正 |
| `docs:` | ドキュメント変更 |
| `chore:` | ビルド・依存関係・補助ツール変更 |
| `refactor:` | 機能変更を伴わないコード整理 |
| `test:` | テスト追加・修正 |
| `ci:` | CI 設定変更 |
| `build:` | ビルドシステム・パッケージ管理変更 |

例: `feat(parse): add Latin Extended-A author surname support`

## セキュリティ

### 機密情報の取り扱い

以下のファイル・情報は**絶対に commit しない**:

- `.env`, `.env.*`, `.envrc`
- `credentials.json`, `service-account*.json`, `client_secret*.json`
- 秘密鍵 (`*.pem`, `*.key`, `id_rsa`, `id_ed25519`)
- API キー・access token を含むあらゆる設定ファイル
- 患者識別情報を含むファイル(本プロジェクトは公開リポジトリのため特に注意)

### 自動防御

- **Layer 1 (Local)**: pre-commit hook で gitleaks が staged 内容を scan
- **Layer 2 (CI)**: GitHub Actions で push/PR 時に再 scan
- **Layer 3 (Audit)**: 定期的な history audit (Day29 で baseline 0 件確認)

### 漏洩発覚時

万が一機密情報を commit してしまった場合:
1. 即座にメンテナに連絡(GitHub Issue または直接連絡)
2. **公開後の漏洩は git history rewrite + force push が必要**
3. 該当する API キー・credential は即座にローテーション

## 関連ドキュメント

- [プロジェクト README](README.md)
- [Day23 LESSONS](docs/sessions/day23/DAY23_LESSONS_LEARNED.md): 機密データ事故と filter-repo 対応の経緯
- [Day29 LESSONS](docs/sessions/day29/DAY29_LESSONS_LEARNED.md): pre-commit gitleaks 導入の経緯
