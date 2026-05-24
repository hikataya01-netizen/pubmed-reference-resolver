# SPEC: Day23 Fixture Remediation (vancouver/mdpi 削除 + Pattern C history rewrite + 新 PMC OA fixture 追加)

**作成日**: 2026-05-24 (Day23 brainstorming 完了時)
**著者**: Claude Code (Opus 4.7 / 1M context) / 承認: 片山英樹
**位置付け**: Day19 Public 切替後に「vancouver_24refs / mdpi_149refs の 2 fixture が査読由来 (input_References.docx が査読 manuscript 起源) で著作権・査読守秘義務上の懸念がある」とユーザー判明したことに伴う remediation
**前提**: Day22 末 (commit `2ddf6cd`、10 Day22 commits 経て v0.1.0 release 公開済) で main branch 105 commits、101 tests passed / 1 skipped。緊急対応として D23-1 で `gh repo edit --visibility private` 実施済、exposure clock 停止済

---

## 1. 背景と目的

### 1.1 検出事象 (brainstorming で判明)

Day22 末のセッションで「`tests/fixtures` に新 sample を入れたい」との user 発話。clarifying questions の中で:

1. 動機が **「著作権の問題」** であり (option 4 を除外して option 3: 査読由来)、新 sample 追加よりも **既存 fixture 入替** が一次目的
2. 該当 fixture は **vancouver_24refs と mdpi_149refs の両方**:
   - `tests/fixtures/vancouver_24refs/input_References.docx` (29819 bytes、Day9 (Z) commit `fe38298` 由来、OneDrive 上の 参照.docx、「親のがん心理影響」24 件 Vancouver style 医学領域)
   - `tests/fixtures/mdpi_149refs/input_References.docx` (39754 bytes、commit `a0bba56` 由来、**README 未作成で出典記述ゼロ**、149 ref corpus)
3. apa_45refs (Day16) と cell_45refs (Day17) は PMC OA CC BY 4.0 で出典明示済 → **影響なし**

### 1.2 Public 公開期間と exposure 範囲

- Day19 (2026-05-21) Public 化 → Day23 (2026-05-24) Private 切替まで **約 3 日間 Public**
- この間に該当 fixture が GitHub から取得可能 (Web UI / git clone / API / archive サービス経由)
- 既に clone した第三者の手元には残置 (これは A/B/C 共通の限界、技術的に手当て不能)

### 1.3 目的

1. **GitHub 上の痕跡を完全消去**: git history rewrite (`git filter-repo`) + `git push --force` で全 commit object から該当 file を strip
2. **test architecture preservation**: vancouver/mdpi スタイルの PMC OA 代替論文を選定し、新 fixture を構築、test coverage を維持
3. **secondary recovery operations**: filter-repo で invalidate される SHA に対応 (.gitleaksignore fingerprint、Day22 archive doc の commit table、v0.1.0 tag、GitHub Release)
4. **再 Public 化**: remediation 完了後に visibility を public へ戻し、v0.1.0 release URL を復活

### 1.4 設計判断の経緯 (brainstorming 質問)

| # | 質問 | 確定 |
|:---:|:---|:---|
| Q1 | 著作権問題の具体 | **(3) 査読由来 (input_References.docx が査読 manuscript 起源)** |
| Q2 | 該当 fixture | **両方 (vancouver_24refs + mdpi_149refs)** |
| Q3 | Remediation Pattern | **(C) Private + history rewrite + force push (完全除去)** |
| Q4 | 即座に Private 切替 | **(推奨) Yes、他の作業より何より Private 切替を先に** → D23-1 で実施済 |
| Q5 | 新 fixture 方針 | **(β) 同スタイル PMC OA 代替を探して test architecture 保持** |
| Q6 | PMC 候補論文の選定方法 | **(1) Claude が PMC 検索して 3-5 件ずつ候補提示、user 選択** |
| Q7 | 実行 timing | **(I) 今日中に全て (Pattern C 実行 + 新 fixture 追加 + 再 Public)** |

---

## 2. Architecture & 全体 phase 構成 (6 phase + 6 checkpoint)

```
[Phase 0: Pre-flight]
  ├ backup 作成 (/tmp/pubmed-reference-resolver_backup_20260524/)
  ├ SHA 記録 (pre-rewrite HEAD / v0.1.0 / log)
  ├ git-filter-repo install (pipx)
  ├ v0.1.0 release notes 保存 (gh release view ... --json body)
  └ checkpoint #1: backup integrity (md5)

[Phase 1: 既存 test/fixture 削除 (通常 commit、filter-repo 対象外で保持)]
  ├ tests/test_integration_vancouver_24refs.py を rm
  ├ tests/test_integration_149refs.py を rm
  ├ tests/fixtures/vancouver_24refs/ を rmtree
  ├ tests/fixtures/mdpi_149refs/ を rmtree
  ├ pytest 実行 → ~92 passed 確認 (元 101 − vancouver 5 − mdpi 4)
  ├ commit chore(remove): vancouver/mdpi fixture and tests
  ├ push origin main (Private repo)
  └ checkpoint #2: HEAD clean, tests green

[Phase 2: filter-repo で history rewrite (destructive、明示承認 gate #A)]
  ├ filter-repo --path tests/fixtures/vancouver_24refs --path tests/fixtures/mdpi_149refs --invert-paths --force
  ├ 検証: git log --all 空、git rev-list 0 hit、du -sh .git で size 削減確認
  └ checkpoint #3: filter-repo 結果 OK

[Phase 3: force push + tag 再付与 (destructive、明示承認 gate #B)]
  ├ git remote add origin (filter-repo が削除した)
  ├ git push --force origin main
  ├ git tag -d v0.1.0 + git push origin :refs/tags/v0.1.0
  ├ git tag -a v0.1.0 <new SHA> -m "..." + git push origin v0.1.0
  ├ gh release delete v0.1.0 + gh release create v0.1.0 (再作成、新 SHA)
  └ checkpoint #4: GitHub state matches local state

[Phase 4: secondary recovery (.gitleaksignore + Day22 archive + memory)]
  ├ .gitleaksignore Day19 fingerprint 4 件 update (52320b6 → 新 SHA)
  ├ gitleaks detect → no leaks found 確認
  ├ Day22 archive (README + LESSONS) の commit table 10 SHA 更新
  ├ memory/project_mdpi_integration.md の SHA 更新 (該当あれば)
  ├ commit + push (新 history 上で)
  └ checkpoint #5: SHA 更新完了、gitleaks clean

[Phase 5: 新 fixture 追加 (PMC 検索 → 構築 → tests)]
  ├ PMC 検索: Vancouver style + 24 ref + CC BY 4.0 → 候補 3-5 件
  ├ PMC 検索: MDPI publisher + 50-150 ref + CC BY 4.0 → 候補 3-5 件
  ├ user 承認後、PMC efetch (JATS XML) → build_*_fixture.py 実行 → input docx 生成
  ├ baseline 生成 (main.py 全 phase 走、LLM cost ~$2-3.5)
  ├ 新 integration test 2 file 追加 (apa/cell 8-test pattern 流用)
  ├ pytest 実行 → ~108 passed (元 92 + 新 vancouver 8 + 新 mdpi 8)
  ├ commit + push
  └ checkpoint #6: 全 tests pass

[Phase 6: 再 Public + Day23 archive]
  ├ gh repo edit --visibility public
  ├ CI status 確認 (gh run list)
  ├ v0.1.0 release URL アクセス確認 (curl)
  ├ docs/sessions/day23/ archive (README + LESSONS) commit + push
  └ Day23 完了
```

---

## 3. Phase 2-3 destructive operation 詳細

### 3.1 Pre-flight (Phase 0)

```bash
# 1. Backup
cp -R /Users/katayamahideki/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver \
      /tmp/pubmed-reference-resolver_backup_20260524/
md5 /tmp/pubmed-reference-resolver_backup_20260524/.git/HEAD > /tmp/day23_backup_md5.txt

# 2. git-filter-repo install
pipx install git-filter-repo  # or: brew install git-filter-repo
git-filter-repo --version

# 3. 現状 SHA 群を記録
git rev-parse HEAD > /tmp/day23_pre_rewrite_head_sha.txt
git rev-parse v0.1.0 > /tmp/day23_pre_rewrite_v010_sha.txt
git log --oneline -20 > /tmp/day23_pre_rewrite_log.txt

# 4. v0.1.0 release notes 保存 (再作成時に再現するため)
gh release view v0.1.0 --json body --jq .body > /tmp/v010_release_notes_day23_restore.md
gh release view v0.1.0 --json name --jq .name > /tmp/v010_release_title.txt
```

### 3.2 filter-repo 実行 (Phase 2 — 明示承認 gate #A)

```bash
# 安全策: filter-repo は自動で origin remote を削除する (force push 暴発防止)
git filter-repo \
  --path tests/fixtures/vancouver_24refs \
  --path tests/fixtures/mdpi_149refs \
  --invert-paths \
  --force  # main repo (not bare clone) なので --force 必要

# 検証 (4 通り)
git log --all --oneline -- tests/fixtures/vancouver_24refs  # 空
git log --all --oneline -- tests/fixtures/mdpi_149refs       # 空
git rev-list --all --objects | grep -c 'tests/fixtures/vancouver_24refs'  # 0
git rev-list --all --objects | grep -c 'tests/fixtures/mdpi_149refs'      # 0

# repo size 削減確認
du -sh .git
```

### 3.3 force push (Phase 3 — 明示承認 gate #B)

```bash
# origin remote 再追加
git remote add origin https://github.com/hikataya01-netizen/pubmed-reference-resolver.git

# branch protection 確認
gh api repos/hikataya01-netizen/pubmed-reference-resolver/branches/main/protection 2>&1 | head -5
# 存在すれば一時 disable

# === DESTRUCTIVE 1: main の force push ===
# CLAUDE.md §7.2.2 で禁止操作の force push を明示承認後に実行
git push --force origin main

# === DESTRUCTIVE 2: v0.1.0 tag 削除と再付与 ===
git push origin :refs/tags/v0.1.0  # remote 削除
git tag -d v0.1.0                   # local 削除

# 新 SHA 上で v0.1.0 を再付与
NEW_V010_SHA=$(git log --oneline | grep "docs(changelog): add Day20 entry" | awk '{print $1}')
git tag -a v0.1.0 "$NEW_V010_SHA" -F /tmp/v010_release_notes_day23_restore.md
git push origin v0.1.0

# === DESTRUCTIVE 3: GitHub Release 再作成 ===
gh release delete v0.1.0 --yes
gh release create v0.1.0 \
  --notes-file /tmp/v010_release_notes_day23_restore.md \
  --title "$(cat /tmp/v010_release_title.txt)"
```

### 3.4 ロールバック手順

```bash
# Phase 2 失敗時 (filter-repo 後で push 前なら local rollback)
rm -rf /Users/katayamahideki/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver
cp -R /tmp/pubmed-reference-resolver_backup_20260524 \
      /Users/katayamahideki/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver
md5 .git/HEAD  # backup と一致確認

# Phase 3 失敗時 (force push 後で GitHub 側との整合性が壊れたら)
git push --force origin main  # local を再強制反映
```

---

## 4. 新 fixture 追加 (Phase 5 詳細)

### 4.1 PMC 検索戦略

**Vancouver-style 代替** (`vancouver_<N>refs`):

検索条件:
- Vancouver/AMA style (numbered, author.title.journal pattern)
- 媒体: 医学領域、PMC OA、CC BY 4.0
- 参考文献数: 24 前後 (旧 fixture と同程度の coverage 維持)
- 領域: ユーザー専門 (緩和ケア/支持療法/がん) を優先候補に

候補生成:
```
NCBI E-utilities:
  esearch.fcgi?db=pmc&term="palliative care"[MeSH]+AND+"open access"[filter]+AND+2024:2026[pdat]
  → 上位 100 件 → 各 PMC ID で efetch (JATS XML) → 参考文献数カウント →
    20-30 ref かつ Vancouver style を 3-5 件抽出
```

**MDPI-style 代替** (`mdpi_<N>refs`):

検索条件:
- MDPI publisher (Cancers, Healthcare, Nutrients, IJERPH, Sensors 等)
- PMC OA + CC BY 4.0 (MDPI default)
- 参考文献数: 50-150 前後
- review 論文優先 (refs が多い)

候補生成:
```
NCBI E-utilities:
  esearch.fcgi?db=pmc&term="cancers"[journal]+OR+"healthcare"[journal]+OR+"nutrients"[journal]
    +AND+"review"[pt]+AND+"open access"[filter]+AND+2024:2026[pdat]
  → 50-150 ref 範囲を 3-5 件抽出
```

候補提示形式 (各 5 件、計 10 件):
```
| # | PMC ID | DOI | Journal | 出版年 | 領域 | ref 数 | LICENSE | タイトル |
|:---|:---|:---|:---|:---:|:---|:---:|:---|:---|
| V1 | PMCxxxx | 10.xxxx | BMC Palliat Care | 2025 | 緩和 | 23 | CC BY | "..." |
| V2 | ...
| M1 | PMCyyyy | 10.yyyy | Cancers (MDPI) | 2026 | 腫瘍 | 87 | CC BY | "..." |
...
```

### 4.2 fixture 構築

既存 `tools/build_apa_fixture.py` / `tools/build_cell_fixture.py` の pattern を踏襲し、2 つの新 tool を作成:

- `tools/build_vancouver_replacement_fixture.py` (apa template ベース)
- `tools/build_mdpi_replacement_fixture.py` (apa template ベース)

各 tool の動作:
1. PMC JATS XML を NCBI efetch でダウンロード
2. `<ref-list>` セクションから各 ref の bibliographic data (factual only) を抽出
3. python-docx で番号付き段落の input_References.docx を生成
4. README.md に出典明示 (apa/cell と同じ表構造、CC BY 4.0 attribution)

**注**: 共通 utility への refactor は Day24+ scope。今日中の Pattern I 制約のため、tool は 2 つ複製で進める。

### 4.3 fixture ディレクトリ命名

旧と同型 `vancouver_<N>refs` / `mdpi_<N>refs` を採用 (filter-repo 後は旧 commit object 一切残らないので path 衝突なし)。新 README で「Day23 で旧 fixture 削除後、新 PMC OA から再構築」と明示。

### 4.4 baseline 生成

```bash
set -a; source skill_package/.env; set +a

# Vancouver replacement: Phase 1-4 全走 (新 fixture なので Phase 3 baseline ない)
python3 main.py tests/fixtures/<new_vancouver>/input_References.docx \
  --output-dir /tmp/<new_vancouver>_baseline_day23
cp /tmp/<new_vancouver>_baseline_day23/{phase3_resolved.json,report.md,three_class_classification.json} \
   tests/fixtures/<new_vancouver>/baseline_*

# Phase 1 baseline は別途生成 (parser-only)
python3 main.py tests/fixtures/<new_vancouver>/input_References.docx \
  --output-dir /tmp/<new_vancouver>_phase1_day23 --phase 1
cp /tmp/<new_vancouver>_phase1_day23/phase1_intermediate.json \
   tests/fixtures/<new_vancouver>/expected_phase1_intermediate.json

# 同様に mdpi replacement
```

LLM cost 見積: Vancouver replacement (~24 refs) ~$0.5、MDPI replacement (~80-149 refs) ~$1.5-3、合計 **~$2-3.5**。

### 4.5 test 追加

`tests/test_integration_apa_45refs.py` を template に複製・改名:
- `tests/test_integration_<new_vancouver>refs.py` (~270 行、8 test pattern)
- `tests/test_integration_<new_mdpi>refs.py` (~270 行、test 8 EXPECTED は実測で確定)

---

## 5. Cross-cutting concerns (Phase 4 詳細)

### 5.1 .gitleaksignore SHA refresh

現状 7 fingerprint のうち、filter-repo の影響を受けるのは Day19 SECRET_SCAN_REPORT の 4 件 (`52320b6...`):

```bash
NEW_DAY19_SHA=$(git log --all --grep="docs(security): add Day19 pre-public secret scan report" --pretty=%H)
OLD_SHA="52320b6d8ad166c4d1ef31ce5c0e608076aad527"
sed -i.bak "s/$OLD_SHA/$NEW_DAY19_SHA/g" .gitleaksignore
diff .gitleaksignore.bak .gitleaksignore  # 4 行変更を確認
rm .gitleaksignore.bak
gitleaks detect --no-banner --redact 2>&1 | tail -3
```

Day8/Day18 由来の 3 fingerprint (`d49dc58`, `c9dce0b`, `8d8c7e3`) は vancouver/mdpi 導入前 commit なので **SHA 不変**、修正不要。

### 5.2 Day22 archive doc の SHA 表更新

`docs/sessions/day22/README.md` + `DAY22_LESSONS_LEARNED.md` の 10 SHA を新 SHA で書き換え:

| 旧 SHA | 識別 |
|:---|:---|
| `c0993f0` | chore(security) Phase A1 |
| `af9e55a` | docs(spec) |
| `d797307` | docs(plan) |
| `301eb9e` | test(nlm) RED |
| `685a600` | fix(nlm) GREEN |
| `f512562` | docs(nlm) fixup |
| `c6e951c` | test(fixtures) |
| `87d054f` | docs(tests) fixup |
| `7d05830` | docs(sessions) Day22 archive |
| `2ddf6cd` | docs(sessions) Day22 fixup |

書換手順:
```bash
# 各 commit の新 SHA を取得 (subject 完全一致 grep)
for old_sha in c0993f0 af9e55a d797307 301eb9e 685a600 f512562 c6e951c 87d054f 7d05830 2ddf6cd; do
  subject=$(git log --all --format="%s" -1 "$old_sha" 2>/dev/null)
  new_sha=$(git log --all --format="%H %s" | grep -F "$subject" | awk '{print $1}')
  echo "$old_sha → $new_sha"
done > /tmp/day23_sha_map.txt

# sed で一括書換
for line in $(cat /tmp/day23_sha_map.txt); do
  old=$(echo $line | awk '{print $1}')
  new=$(echo $line | awk '{print $3}')
  sed -i.bak "s/$old/${new:0:7}/g" docs/sessions/day22/README.md docs/sessions/day22/DAY22_LESSONS_LEARNED.md
done
rm docs/sessions/day22/*.bak

# 残存チェック (0 hit が期待)
grep -E "c0993f0|af9e55a|d797307|301eb9e|685a600|f512562|c6e951c|87d054f|7d05830|2ddf6cd" docs/sessions/day22/
```

### 5.3 memory file の SHA 更新

`/Users/katayamahideki/.claude/projects/-Users-katayamahideki-Desktop-Claude-------reference--pubmed-reference-resolver/memory/project_mdpi_integration.md` に `HEAD 1dbf9d7` 記載あり (Day22 確認時点)。filter-repo 後は新 SHA に更新:

```bash
grep -rn "1dbf9d7\|c0993f0\|af9e55a\|d797307\|301eb9e\|685a600\|f512562\|c6e951c\|87d054f\|7d05830\|2ddf6cd" \
  ~/.claude/projects/-Users-katayamahideki-Desktop-Claude-------reference--pubmed-reference-resolver/memory/
# 該当あれば新 SHA で update
```

### 5.4 CI 整合性

`.github/workflows/tests.yml` は変更不要:
- `pip install -r requirements.txt` — 不変
- `python -m pytest tests/ -q` — 新 test 自動収集

filter-repo 後の push 時、GitHub Actions が新 SHA に対して run を起動。旧 SHA の Actions runs は GitHub UI に残るが、commit との reverse link は壊れる (影響軽微)。

---

## 6. 完了条件 (15 項目)

| # | 条件 | 確認方法 |
|:---:|:---|:---|
| 1 | repo 一時 Private 化 完了 | `gh repo view ... --json isPrivate` = true (D23-1 完了済) |
| 2 | backup 作成 + integrity 確認 | `/tmp/pubmed-reference-resolver_backup_20260524/` 存在 + md5 一致 |
| 3 | Phase 1 test/fixture 削除 commit | `chore(remove): vancouver/mdpi fixture and tests` が HEAD |
| 4 | filter-repo 後 vancouver_24refs が history 完全消失 | `git log --all -- tests/fixtures/vancouver_24refs` 空 |
| 5 | filter-repo 後 mdpi_149refs が history 完全消失 | 同上 |
| 6 | force push 成功 (main + tag) | `gh api repos/.../commits/main --jq .sha` = local HEAD |
| 7 | v0.1.0 tag 再付与 + GitHub Release 再作成 | `gh release view v0.1.0` 存在、`isDraft: false` |
| 8 | .gitleaksignore Day19 fingerprint 4 件 update | `grep 52320b6 .gitleaksignore` 0 hit、新 SHA で 4 行存在 |
| 9 | gitleaks scan clean | `gitleaks detect --no-banner --redact` = no leaks found |
| 10 | Day22 archive doc の 10 SHA update | `grep -c '<old SHA>' docs/sessions/day22/` 0 hit |
| 11 | memory file の SHA update | memory grep で旧 SHA 0 hit |
| 12 | 新 Vancouver replacement fixture + 8 tests | README 存在 + integration test 8 件 pass |
| 13 | 新 MDPI replacement fixture + 8 tests | 同上 |
| 14 | 全 tests pass (regression なし) | `pytest tests/ -q` = ~108 passed, 1 skipped |
| 15 | 再 Public + CI green + release URL 200 | `gh repo view --json visibility` = PUBLIC + CI success + curl 200 |

---

## 7. Commit 計画 (8-12 commits)

| 順 | Phase | type | 内容 |
|:---:|:---:|:---|:---|
| 1 | 1 | `chore(remove)` | vancouver/mdpi fixture + test 削除 |
| — | 2 | (no commit) | filter-repo (history rewrite) |
| — | 3 | (no commit) | force push + tag 再付与 |
| 2 | 4 | `chore(security)` | .gitleaksignore Day19 fingerprint refresh |
| 3 | 4 | `docs(sessions)` | Day22 archive の SHA 表更新 |
| 4 | 4 | `chore(memory)` | memory file SHA update (該当あれば) |
| 5 | 5 | `feat(tools)` | tools/build_<new>_fixture.py × 2 追加 |
| 6 | 5 | `test(fixtures)` | 新 Vancouver replacement fixture |
| 7 | 5 | `test(integration)` | tests/test_integration_<new_vancouver>refs.py |
| 8 | 5 | `test(fixtures)` | 新 MDPI replacement fixture |
| 9 | 5 | `test(integration)` | tests/test_integration_<new_mdpi>refs.py |
| 10 | 6 | `docs(sessions)` | Day23 archive (README + LESSONS) |
| (任意) | 6 | `chore(release)` | CHANGELOG.md に Day23 entry |

---

## 8. 工数見積もり

| Phase | 内容 | 見積 |
|:---:|:---|---:|
| 0 | Pre-flight | 15 min |
| 1 | test/fixture 削除 + commit + push | 20 min |
| 2 | filter-repo + 検証 | 20 min |
| 3 | force push + tag/release 再作成 | 30 min |
| 4 | secondary recovery (.gitleaksignore + Day22 doc + memory) | 40 min |
| 5a | PMC 検索 + 候補提示 | 30 min |
| 5b | user 選定 + download + build_*_fixture.py | 60 min |
| 5c | baseline 生成 (LLM ~$2-3.5) + README | 90 min |
| 5d | 新 integration test 2 file 追加 | 60 min |
| 6 | Day23 archive + 再 Public + 最終確認 | 45 min |
| **合計** | | **~6.5h** |

LLM cost: ~$2.2-3.7

---

## 9. 想定リスク

| リスク | 確率 | 影響 | 対応 |
|:---|:---:|:---:|:---|
| backup 取得時の disk full | 低 | 致命 | 事前 `df -h` 確認、最低 1GB 空き |
| filter-repo 後の検証で残存検出 | 中 | 高 | backup から復旧、`--path` を見直し |
| force push 後の CI failure | 中 | 中 | inline fix or backup から復旧 |
| v0.1.0 release notes 再現で content drift | 低 | 低 | Phase 0 で `gh release view --json body` 保存 |
| branch protection 有効で force push 失敗 | 中 | 中 | 事前 `gh api .../branches/main/protection` 確認、一時 disable |
| PMC 検索で適切な候補が 5 件揃わない | 中 | 中 | 検索 query を緩める、候補 2-3 件でも user 決定すれば進む |
| MDPI 149-ref 相当の候補が見つからない | 中 | 低 | 50-80 ref で妥協、test 8 期待値は実測で |
| Day24 まで Private のまま終わるリスク | 低 | 中 | Phase 6 で再 Public 化を忘れない (完了条件 #15) |
| 本日中に Phase 5 終わらず Phase 6 が翌日 | 中 | 低 | Day23 archive に「Public 化は Day24 朝に persist」記載、Phase 1-4 完了で機密性は確保済 |

---

## 10. Out of Scope (Day24+)

- pre-commit hook gitleaks 自動実行 (Day22 handoff パターン 3)
- CONTRIBUTING.md / Issue PR template (Day22 handoff パターン 2)
- PyPI 公開 (v0.2.0 候補)
- pyproject.toml + uv.lock 移行 (CLAUDE.md §8 整合)
- Crossref graceful failure 16 件の対応 (Day22 §6.3 NEW)
- NLM fuzzy-match precision 改善 (Day22 §6.3 NEW)
- tools/build_*_fixture.py の共通 utility への refactor

---

## 11. 参照

- Day9 LESSONS: `docs/sessions/day9/DAY9_LESSONS_LEARNED.md` (vancouver_24refs の origin context)
- Day11 LESSONS: `docs/sessions/day11/DAY11_LESSONS_LEARNED.md` (fixture 命名規約 hybrid)
- Day16 SPEC: `docs/sessions/day16/SPEC_apa_45refs_fixture.md` (apa fixture build pattern, 模範)
- Day17 SPEC: `docs/sessions/day17/SPEC_cell_45refs_fixture.md` (cell fixture build pattern, 模範)
- Day19 SECRET_SCAN_REPORT: `docs/sessions/day19/SECRET_SCAN_REPORT.md` (.gitleaksignore Day19 fingerprint の出典)
- Day22 archive: `docs/sessions/day22/` (10 SHA chain、本 spec で更新対象)
- Day22 brainstorming spec: `docs/superpowers/specs/2026-05-24-rule3-nlm-ssl-fix-design.md` (本 spec と同 day の先行 spec)
- CLAUDE.md §7.2.2: 破壊的 git 操作の禁止事項 (force push, filter-repo, force-with-lease 等)
- CLAUDE.md §7.3: 院内・患者情報の取扱い (本 spec の confidentiality 概念に近接)
- git-filter-repo: https://github.com/newren/git-filter-repo (公式 documentation)

---

**承認**: 片山英樹 (brainstorming Q1-Q7 + design 全 5 sections)
**次工程**: writing-plans skill で bite-sized implementation plan を作成
