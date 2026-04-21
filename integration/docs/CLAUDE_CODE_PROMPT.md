# Claude Code への指示プロンプト (テンプレート集)

本ファイルは、本セッションで開発した修正内容を Claude Code で本体スキル
(`~/.claude/skills/pubmed-reference-resolver/` 等) に統合する際に、
Claude Code に渡すプロンプトのテンプレート集です。

**使い方**:
1. 本パッケージ全体 (`integration/` ディレクトリ) を、本体スキルのリポジトリ
   ルートに `integration/` として配置するか、別の作業ディレクトリに展開する
2. 以下のテンプレートのうち、段階的に適用したいものを選んで Claude Code に
   貼り付ける
3. 各ステップの完了を確認してから次に進む (一度に全部投げない)

---

## 🎯 推奨プロンプト (段階的統合, 7 ステップ)

以下のプロンプトは「1 コミット = 1 プロンプト」対応。
Claude Code は各ステップ完了後に git commit まで行う想定。

### ステップ 0: 事前準備 (ブランチ作成)

```
pubmed-reference-resolver スキルに新機能を段階的に統合するため、作業ブランチを
作成してください。

- ブランチ名: feature/mdpi-fast-path
- ベース: 現在の main/master ブランチの HEAD

その後、integration/ ディレクトリにある以下のファイルを読んで、全体像を
把握してください:
- integration/INTEGRATION_BRIEF.md  ← 統合計画の全体像
- integration/src/mdpi_parser.py    ← 新規モジュール
- integration/src/journal_audit.py  ← 新規モジュール
- integration/patches/01_split_references_fix.patch
- integration/patches/02_mdpi_fast_path.patch

読み終えたら、統合計画に対するあなたの懸念点や、実装順序について改善案が
あれば教えてください。私が同意してから次のステップに進みます。
```

---

### ステップ 1: Phase 1 バグ修正

```
Commit 1 を実施してください。

1. integration/patches/01_split_references_fix.patch を main.py に適用する
   (patch 適用に失敗する場合は、パッチを参考に手動で相当する変更を加える)

2. 以下のテストを tests/test_split_references_doi_boundary.py として新規追加:
   - References.docx のような「DOI で終わる ref の直後に次 ref が来る」
     ケースで、ブロックが正しく 2 つに分離されることを検証
   - integration/tests/test_integration_149refs/input_References.docx を
     tests/fixtures/ にコピーして、そこから Phase 1 を走らせ、149 ブロックが
     得られることを assertion

3. pytest を走らせて緑を確認

4. git add . && git commit -m (INTEGRATION_BRIEF.md の Commit 1 メッセージを使用)

完了したら「Step 1 done」と報告してください。
```

---

### ステップ 2: MDPI パーサモジュール追加

```
Commit 2 を実施してください。

1. integration/src/mdpi_parser.py をスキルのルートディレクトリにコピーする

2. コピー後、スキル固有のコーディング規約 (main.py のスタイル) に合わせて
   微調整してください。特に:
   - import 順序 (stdlib → 3rd party → local の並び)
   - 型ヒントのスタイル (dict[str, Any] vs Dict[str, Any] 等)
   - docstring の書式 (Google スタイル vs NumPy スタイル)

3. tests/test_mdpi_parser.py を integration/tests/ からコピーし、
   from 文をスキルのパッケージ名に合わせて調整してください

4. integration/tests/test_integration_149refs/ 全体を tests/fixtures/mdpi_149refs/
   にコピーしてください (ゴールドスタンダードデータ)

5. pytest tests/test_mdpi_parser.py -v を実行し、全テストが緑になることを確認
   もし test_mdpi_parser_149refs_full_pipeline が失敗する場合、期待 JSON との
   差分を調査し、パーサ改善が必要か、期待 JSON の更新が必要かを判断する
   (どちらを選ぶべきか、あなたの判断を添えて提案してください)

6. 緑になったら git commit

完了したら「Step 2 done」と報告してください。
```

---

### ステップ 3: structure_all_references への fast-path 統合

```
Commit 3 を実施してください。

1. integration/patches/02_mdpi_fast_path.patch を main.py に適用する
   (手動編集でも可)

2. 適用後、以下の挙動を確認:
   a) MDPI 形式の References.docx (tests/fixtures/mdpi_149refs/input_References.docx)
      を処理し、ANTHROPIC_API_KEY が未設定でも正常完走すること
   b) 既存の Vancouver/AMA 形式のテストデータ (もしあれば) がまだ LLM 経由で
      正常に処理されること

3. 既存の examples/expected_output/ のゴールドデータが MDPI fast-path で
   微妙に変わる可能性がある。差分がある場合、以下のどちらかを選ぶ:
   a) パーサを改善してゴールドに合わせる
   b) ゴールドを更新する (変化が合理的な場合)
   どちらを選んだか、理由を添えて報告してください

4. git commit

完了したら「Step 3 done」と、a) ゴールドデータに対する差分要約、
b) MDPI fast-path の適用率 (全ブロック中何%が fast-path になったか) を
報告してください。
```

---

### ステップ 4: manual_overrides.yaml サポート

```
Commit 4 を実施してください。

1. integration/src/manual_overrides.yaml をスキルルートに
   manual_overrides.yaml.example としてコピー (ユーザーテンプレート扱い)

2. main.py CLI に --overrides PATH 引数を追加。指定時に YAML を読み込んで
   structure_all_references(overrides=...) に渡す

3. pyyaml は optional dependency として扱う:
   - 指定されたが pyyaml 未インストール → エラーで中止
   - 未指定 → そのまま動く (pyyaml import しない)

4. tests/test_manual_overrides.py を新規追加:
   - YAML に ref_no マッチの override を書き、処理結果に反映されること
   - DOI マッチの override も同様

5. git commit

完了したら「Step 4 done」と報告してください。
```

---

### ステップ 5: journal_audit モジュール追加

```
Commit 5 を実施してください。

1. integration/src/journal_audit.py をスキルルートにコピー

2. スキルのスタイルに合わせて微調整 (ステップ 2 と同様)

3. tests/test_journal_audit.py を新規追加:
   - Ref #13 相当のケース (citation journal と PubMed journal_iso が 44% 類似度)
     で MAJOR finding が生成されることを確認
   - 類似度 85% のケース (単なる略称揺れ) では OK になって除外されることを確認

4. pytest 緑確認 → git commit

完了したら「Step 5 done」と報告してください。
```

---

### ステップ 6: Stage 5 (report.md) への統合

```
Commit 6 を実施してください。

1. main.py の run_phase4() (report.md 合成処理) の末尾に、journal_audit の
   呼び出しを追加:
   ```python
   from . import journal_audit
   findings = journal_audit.audit_journal_mismatch(
       result["stage3_structured"],
       result["stage4_pubmed_resolutions"],
   )
   report_md += journal_audit.format_findings_markdown(findings)
   ```

2. result["stage5_journal_audit"] = findings も追加して、JSON ダンプにも
   含まれるようにする

3. References.docx で動作確認:
   - report.md に "## 補遺: ジャーナル名と PubMed 収載誌の照合監査" セクションが
     出ること
   - Ref #13 が MAJOR で出ること

4. tests/test_integration_149refs/expected_report.md を、本セッション生成の
   report.md (integration/tests/test_integration_149refs/expected_report.md) に
   差し替え、回帰テストで比較

5. git commit

完了したら「Step 6 done」と、実際に生成された report.md の該当セクションを
引用して報告してください。
```

---

### ステップ 7: CI 設定

```
Commit 7 を実施してください。

1. .github/workflows/test.yml (存在しなければ新規作成) に:
   - Python 3.11 セットアップ
   - pip install -r requirements.txt
   - pytest tests/ -v
   のジョブを定義

2. requirements.txt に rapidfuzz, pyyaml (optional marker 付き) があることを確認

3. ローカルで全テスト緑を確認してから push

4. PR を作成: feature/mdpi-fast-path → main
   PR 本文には INTEGRATION_BRIEF.md の「検証チェックリスト」をコピーして
   チェックボックス形式で記載

完了したら「Step 7 done」と、PR の URL を報告してください。
```

---

## 🚀 一括実施プロンプト (時短したい場合)

時間が限られる場合、段階的ではなく一括で進める指示も可能です。ただし問題
発生時のロールバックが難しくなるため、慣れた方向け。

```
integration/ ディレクトリ全体を読み、INTEGRATION_BRIEF.md の統合計画に
従って、Commit 1 から Commit 7 まで順次実施してください。各ステップ
完了時に短いサマリ (変更ファイル数、テスト結果、警告) を報告し、エラーや
不明点があれば即座に停止して確認を求めてください。

作業ブランチ: feature/mdpi-fast-path
最終成果: pytest 全緑 + PR 作成

途中で本体コードに手を入れる必要が生じた場合 (例: 既存 examples/expected_output/
のゴールドデータ更新)、勝手に更新せず、差分の性質と判断根拠を説明してから
確認を取ってください。
```

---

## 🔍 デバッグ用プロンプト

### パッチ適用エラー時

```
integration/patches/XX_yyy.patch の適用が失敗しました。パッチ内容と現在の
main.py を比較し、原因 (行番号ずれ、既存の差分、context mismatch など) を
特定してください。その後、以下のいずれかで対応:

1. 手動で相当する変更を main.py に施す (推奨、パッチの意図を保持)
2. パッチを現状コードに合わせて再生成する

どちらを選んだか、変更内容の要約と共に報告してください。
```

### テスト失敗時

```
pytest が失敗しました。失敗したテストの出力全文を貼り付け、以下を分析:

1. 期待値と実際値の差分
2. 差分の原因 (パーサのバグ / ゴールドデータの古さ / 環境差異)
3. 修正方針 (コード修正 or ゴールド更新 or テスト緩和)

分析結果を報告してから修正に進んでください。
```

---

## 💡 統合後のメンテナンス

統合完了後、以下のシナリオで再度このパッケージが役立つ可能性があります:

- **新しい MDPI 形式 Reference 論文で誤パースが発生**: tests/fixtures/
  に新しいゴールドケースを追加し、mdpi_parser.py を改善
- **新しい引用スタイル (Vancouver, APA) に対応**: 新規 parser モジュール
  (vancouver_parser.py 等) を同じ設計で追加し、is_vancouver_style() で
  fast-path 判定を拡張
- **journal_audit の精度改善**: NLM の journal abbreviation database
  (https://www.ncbi.nlm.nih.gov/nlmcatalog/journals) を取り込み、略称の
  正規化を強化

---

**以上**。本プロンプトテンプレートは、各ステップが終わるたびに Claude Code
との対話の中で微調整されることを想定しています。必要に応じて修正してお使い
ください。
