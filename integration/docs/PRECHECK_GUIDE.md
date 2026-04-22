# パッチ事前チェック ガイド (予行演習)

本ガイドは、統合パッケージを Claude Code に投げる前に **先生のローカル環境で
パッチが適用可能かを事前確認**する手順を説明します。

---

## なぜ予行演習するのか

`git apply --check` で事前チェックすることで:

1. **行番号ずれや空白差で適用失敗する場合を統合前に発見**できる
2. **問題があれば、Claude Code に投げる前に対処方針を決められる**
3. **手で修正する選択肢を残せる** (パッチ再生成 vs 手動適用の判断)

本セッションでも実際に予行演習を実施し、2 つの重要問題を発見しました。
詳細は本ガイド末尾の「本セッションで発見された問題」を参照。

---

## 前提条件

- 先生のローカルで `pubmed-reference-resolver` スキルが **Git 管理されている** こと
  - 管理されていない場合は、以下のいずれかで Git 管理下に置く:

    ```bash
    cd ~/claude-skills/pubmed-reference-resolver/   # あるいは先生のスキル置き場
    git init
    git add -A
    git commit -m "Initial commit (pre-integration baseline)"
    ```

- Python 3.11+ と、既存スキルの依存 (`pypdf`, `python-docx`, `requests`,
  `rapidfuzz`, `tenacity`) がインストール済みであること

---

## 手順

### Step 1: 作業ブランチを作る

```bash
cd ~/claude-skills/pubmed-reference-resolver/  # パスは先生の環境に合わせて
git status                                     # 現状クリーンであることを確認
git checkout -b feature/mdpi-fast-path         # 作業ブランチ作成
git branch                                     # → "* feature/mdpi-fast-path" と表示されれば OK
```

### Step 2: 統合パッケージを配置

```bash
# zip を展開していない場合
cd ~/claude-skills/pubmed-reference-resolver/
unzip ~/Downloads/pubmed-resolver-integration-v1.zip

# 配置確認
ls integration/patches/
# → 01_split_references_fix.patch
# → 02_mdpi_fast_path.patch
```

### Step 3: 各パッチを事前チェック

```bash
# Patch 01
git apply --check integration/patches/01_split_references_fix.patch
echo "終了コード: $?"
# 0 なら適用可能
# 0 以外ならエラー出力を読んで対処 (後述)

# Patch 02
git apply --check integration/patches/02_mdpi_fast_path.patch
echo "終了コード: $?"
```

### Step 4: 結果の判定と分岐

#### パターン A: 両方とも終了コード 0

→ そのまま Claude Code に投げて問題なし。`docs/CLAUDE_CODE_PROMPT.md` の
Step 1 から進める。

#### パターン B: 片方または両方が失敗

→ 以下の対処法へ。

---

## パッチ失敗時の対処法

### 対処 1: パッチを実コードから再生成する (推奨)

`git apply --check` が失敗した場合、**パッチの意図を Python で直接コードに
適用**し、`git diff` でクリーンなパッチを再生成するのが最も確実です。

```bash
# 例: Patch 01 の意図 = split_references の lookahead 拡張
python3 << 'PYEOF'
from pathlib import Path
p = Path("main.py")
txt = p.read_text(encoding="utf-8")

# 変更対象の元コード (完全一致が必要)
old = '    matcher = re.compile(r"(?<![\\d.])(\\d+)[\\.\\s]+(?=[A-Z])")'

# 変更後のコード
new = (
    '    # NOTE: lookahead allows lowercase prefixes (van, de, ...)\n'
    '    matcher = re.compile(\n'
    '        r"(?<![\\d.])(\\d+)[\\.\\s]+"\n'
    '        r"(?=[A-Z]|van\\s|de\\s+[A-Z]|du\\s+[A-Z]|den\\s+[A-Z]|von\\s+[A-Z])"\n'
    '    )'
)
assert old in txt, "置換対象が見つからない (元コードが既に変わっている可能性)"
p.write_text(txt.replace(old, new), encoding="utf-8")
print("✓ 適用完了")
PYEOF

# クリーンなパッチを再生成
git diff main.py > integration/patches/01_split_references_fix_V2.patch

# 再チェック (前の変更を戻してから)
git checkout main.py
git apply --check integration/patches/01_split_references_fix_V2.patch
# 終了コード 0 になる
```

### 対処 2: `--reject` オプションで部分適用

```bash
git apply --reject integration/patches/01_split_references_fix.patch
# 適用できた部分はファイルに反映
# 失敗した hunk は .rej ファイルに残る
ls *.rej
# → main.py.rej

# .rej ファイルを開いて、手動で該当箇所に適用
vim main.py
# ... 手動編集 ...

# 適用後に .rej を削除
rm main.py.rej
```

### 対処 3: Claude Code に直接手動編集を依頼

パッチを諦め、INTEGRATION_BRIEF.md の「変更意図」だけを Claude Code に
説明して、コードを直接編集してもらう:

```
integration/patches/01_split_references_fix.patch の適用が失敗しました。
main.py の split_references() 関数内の正規表現 lookahead を修正したいです。

目的:
 '(?=[A-Z])' を '(?=[A-Z]|van\\s|de\\s+[A-Z]|du\\s+[A-Z]|den\\s+[A-Z]|von\\s+[A-Z])'
 に置き換えたいです。これは Dutch/French lowercase-prefixed な著者
 (van der Biessen, van Zyl 等) を捕捉するため。

matcher と standard (fallback) の 2 箇所あるので、両方とも修正してください。
修正後、tests/fixtures/mdpi_149refs/input_References.docx で Phase 1 を走らせ
149 件が検出されることを確認してください。
```

---

## 動作検証 (パッチ適用後)

パッチ適用に成功したら、実データで動作を確認:

```bash
# tests/ に配置したゴールドデータを使う (Step 2 で展開済み)
python3 << 'PYEOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
import main

docx = Path("integration/tests/test_integration_149refs/input_References.docx")
raw, _ = main.extract_text(docx)
ln = main.detect_line_numbers(raw)
cleaned, _ = main.preprocess(raw, ln)
blocks = main.split_references(cleaned)

print(f"検出ブロック数: {len(blocks)}")
missing = [n for n in range(1, 150) if n not in [b.ref_no for b in blocks]]
print(f"欠落: {missing}")
assert len(blocks) == 149, "149 件揃わず"
assert not missing, f"欠落あり: {missing}"
print("✓ Phase 1 動作検証 PASS")
PYEOF
```

---

## チェックリスト

パッチ適用の予行演習が完了したら、以下を確認:

- [ ] `git apply --check` で両パッチとも終了コード 0
- [ ] 失敗したパッチについては V2 として再生成するか、手動適用の方針決定済み
- [ ] 適用後に Phase 1 で 149/149 件が検出される
- [ ] `git status` で予期しないファイル変更がない
- [ ] `git log` で baseline コミットが残っている (rollback 可能な状態)

全てクリアしたら、`docs/CLAUDE_CODE_PROMPT.md` の Step 1 から Claude Code に
投げ始めてください。

---

## 本セッションで発見された問題

予行演習によって、以下の重要問題が統合前に発見されました:

### 問題 1: Patch 01 が corrupt patch エラー

- **原因**: 手書きパッチのフォーマット不整合 (context の空白や改行)
- **対処**: 対処 1 (Python 置換 → git diff 再生成) で V2 を作成

### 問題 2: 当初のパッチが機能的に不十分

- **原因**: `split_references` の取りこぼしは LIS 由来と誤診断していたが、
  実際は **lookahead `(?=[A-Z])` が lowercase prefix の姓 (van, de 等) を
  拒否**していた
- **影響**: References.docx Ref #40 (van der Biessen), Ref #140 (van Zyl)
- **対処**: lookahead パターンを拡張して Dutch/French 姓を許容

**→ 現在の `patches/01_split_references_fix.patch` は V2 相当の正しい版です**

---

**以上**。予行演習は統合作業の保険として強く推奨します。15 分の事前投資で
数時間の手戻りを回避できます。
