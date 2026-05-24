# Day23 Fixture Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove vancouver_24refs + mdpi_149refs fixtures (peer-review-derived, confidentiality concern) from GitHub via `git filter-repo` + `git push --force`, refresh SHA-dependent metadata (`.gitleaksignore`, Day22 archive doc), then construct replacement fixtures from PMC OA CC BY 4.0 papers preserving the test architecture, then re-publish the repo.

**Architecture:** 6-phase sequential workflow (Pre-flight → Soft delete → filter-repo → force push → Secondary recovery → New fixtures → Re-public). Two destructive operations (Phase 2: filter-repo, Phase 3: force push) are gated by explicit user approval. New fixtures follow existing `build_apa_fixture.py` / `build_cell_fixture.py` patterns and the 8-test integration template from `tests/test_integration_apa_45refs.py`.

**Tech Stack:** Python 3.11+ (3.14 local), git-filter-repo (new, install via brew), `gh` CLI, NCBI E-utilities (PMC efetch/esearch), python-docx, pytest 9.x, urllib + certifi (from Day22).

**Spec reference:** `docs/superpowers/specs/2026-05-24-day23-fixture-remediation-design.md` (commit `b366287`)

**Pre-rewrite state:**
- HEAD: `b366287` (Day23 spec commit)
- v0.1.0 tag SHA: `c68cad0` (will be invalidated by filter-repo)
- Repo visibility: PRIVATE (D23-1 で切替済、Phase 6 で再 Public 化)
- 全 tests: 101 passed / 1 skipped
- 7 .gitleaksignore fingerprints (4 will need refresh after filter-repo)

**Total commits:** 12 (1 spec + 1 plan + 10 implementation; spec already committed as #1)

---

## File Structure

### Files DELETED in Phase 1 (will also be stripped from history in Phase 2)

| File / Directory | Why |
|:---|:---|
| `tests/fixtures/vancouver_24refs/` (entire dir, 5 files) | Peer-review-derived input docx, confidentiality concern |
| `tests/fixtures/mdpi_149refs/` (entire dir, 6 files) | Peer-review-derived input docx, confidentiality concern |
| `tests/test_integration_vancouver_24refs.py` | Test for deleted fixture |
| `tests/test_integration_149refs.py` | Test for deleted fixture |

### Files MODIFIED in Phase 4 (after filter-repo, secondary recovery)

| File | Why |
|:---|:---|
| `.gitleaksignore` | Day19 SECRET_SCAN_REPORT fingerprint SHA `52320b6…` invalidated by filter-repo; replace 4 lines with new SHA |
| `docs/sessions/day22/README.md` | Commit table contains 10 SHAs (`c0993f0`…`2ddf6cd`) all invalidated; replace with new SHAs |
| `docs/sessions/day22/DAY22_LESSONS_LEARNED.md` | §3 commit chain contains same 10 SHAs; replace |
| `~/.claude/projects/.../memory/project_mdpi_integration.md` | Possibly contains `1dbf9d7` or other old SHAs (verify with grep, update if found) |

### Files CREATED in Phase 5 (new fixtures + new tests + new build tools)

| File | Why |
|:---|:---|
| `tools/build_vancouver_replacement_fixture.py` | New PMC OA Vancouver-style fixture builder (apa_fixture template) |
| `tools/build_mdpi_replacement_fixture.py` | New PMC OA MDPI-style fixture builder (apa_fixture template) |
| `tests/fixtures/vancouver_<N>refs/` (new dir, ~5 files) | Replacement Vancouver fixture (input docx + 3 baseline files + README) |
| `tests/fixtures/mdpi_<N>refs/` (new dir, ~5 files) | Replacement MDPI fixture |
| `tests/test_integration_vancouver_<N>refs.py` | 8-test integration template applied to new Vancouver |
| `tests/test_integration_mdpi_<N>refs.py` | 8-test integration template applied to new MDPI |

### Files CREATED in Phase 6 (Day23 archive)

| File | Why |
|:---|:---|
| `docs/sessions/day23/README.md` | Day23 session index |
| `docs/sessions/day23/DAY23_LESSONS_LEARNED.md` | Day23 retrospective (D23-1 lessons captured) |

### Files NOT TOUCHED

`nlm_catalog_check.py`, `main.py`, `crossref_check.py`, `journal_audit.py`, `mdpi_parser.py`, `three_class_classifier.py`, `requirements.txt`, `tests/test_nlm_catalog_check.py`, `tests/test_integration_apa_45refs.py`, `tests/test_integration_cell_45refs.py`, all fixtures under `apa_45refs/` + `cell_45refs/` + `three_class_classification/`, Day1-21 archive docs.

---

## Task 0: Commit this plan

**Files:**
- Modify: `docs/superpowers/plans/2026-05-24-day23-fixture-remediation.md` (just written)

- [ ] **Step 1: Stage and review**

```bash
git add docs/superpowers/plans/2026-05-24-day23-fixture-remediation.md
git status --short
```

Expected: 1 file added under `docs/superpowers/plans/`.

- [ ] **Step 2: Commit**

```bash
git commit -m "$(cat <<'EOF'
docs(plan): add Day23 fixture remediation implementation plan

spec (commit b366287) に基づく 10 commit + bite-sized step の実装計画.

主要 task:
  - Task 1: Phase 0 Pre-flight (backup + SHA snapshot + filter-repo install)
  - Task 2: Phase 1 vancouver/mdpi の test+fixture 削除 commit
  - Task 3 (Gate #A): Phase 2 filter-repo 実行 (destructive)
  - Task 4 (Gate #B): Phase 3 force push + v0.1.0 tag/release 再作成 (destructive)
  - Task 5-7: Phase 4 secondary recovery (.gitleaksignore + Day22 doc + memory)
  - Task 8: Phase 5a PMC 検索 + user 選定
  - Task 9: Phase 5b 新 fixture 構築 (build tools + baseline)
  - Task 10: Phase 5c 新 integration test
  - Task 11: Phase 6 再 Public + Day23 archive

Phase 2/3 は CLAUDE.md §7.2.2 で禁止された force push を含むため、各
task の前に明示承認 gate を設置.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 3: Verify**

Run: `git log --oneline -2`
Expected: HEAD = this commit (docs(plan)…), HEAD~1 = `b366287` (docs(spec)…).

---

## Task 1: Phase 0 Pre-flight

**Goal:** Create backup, snapshot pre-rewrite SHAs, save v0.1.0 release notes, install git-filter-repo.

**Files:**
- Create: `/tmp/pubmed-reference-resolver_backup_20260524/` (cp -R of working tree)
- Create: `/tmp/day23_backup_md5.txt`, `/tmp/day23_pre_rewrite_head_sha.txt`, `/tmp/day23_pre_rewrite_v010_sha.txt`, `/tmp/day23_pre_rewrite_log.txt`, `/tmp/v010_release_notes_day23_restore.md`, `/tmp/v010_release_title.txt`

- [ ] **Step 1: Check disk space**

```bash
df -h /tmp /Users/katayamahideki | tail -5
```

Expected: at least 1 GiB available on both. If less, stop and free space before proceeding.

- [ ] **Step 2: Create repo backup**

```bash
cp -R /Users/katayamahideki/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver \
      /tmp/pubmed-reference-resolver_backup_20260524/
md5 /tmp/pubmed-reference-resolver_backup_20260524/.git/HEAD > /tmp/day23_backup_md5.txt
cat /tmp/day23_backup_md5.txt
```

Expected: md5 hash printed. Working tree copy at `/tmp/.../`.

- [ ] **Step 3: Snapshot pre-rewrite SHAs**

```bash
git rev-parse HEAD > /tmp/day23_pre_rewrite_head_sha.txt
git rev-parse v0.1.0 > /tmp/day23_pre_rewrite_v010_sha.txt
git log --oneline -20 > /tmp/day23_pre_rewrite_log.txt
cat /tmp/day23_pre_rewrite_head_sha.txt /tmp/day23_pre_rewrite_v010_sha.txt
```

Expected: HEAD = (whatever HEAD is after Task 0 commit, e.g., `<new>`), v0.1.0 = `c68cad00a2e780400045d2bacee0b68cb76a2039`.

- [ ] **Step 4: Save v0.1.0 release notes (for re-creation in Phase 3)**

```bash
gh release view v0.1.0 --json body --jq .body > /tmp/v010_release_notes_day23_restore.md
gh release view v0.1.0 --json name --jq .name > /tmp/v010_release_title.txt
wc -l /tmp/v010_release_notes_day23_restore.md
cat /tmp/v010_release_title.txt
```

Expected: release notes file ~50-60 lines, title = `v0.1.0 — Day1-20 統合スナップショット (Day7 §9.3 完全クローズ)`.

- [ ] **Step 5: Install git-filter-repo via brew**

```bash
brew install git-filter-repo
git-filter-repo --version
```

Expected: version 2.x.x printed. If `brew install` fails (e.g., outdated formulae), run `brew update` first.

- [ ] **Step 6: Verify pre-flight checklist**

Run:
```bash
ls -la /tmp/pubmed-reference-resolver_backup_20260524/.git/HEAD \
       /tmp/day23_backup_md5.txt \
       /tmp/day23_pre_rewrite_head_sha.txt \
       /tmp/day23_pre_rewrite_v010_sha.txt \
       /tmp/day23_pre_rewrite_log.txt \
       /tmp/v010_release_notes_day23_restore.md \
       /tmp/v010_release_title.txt
which git-filter-repo
```

Expected: all 7 files exist + filter-repo path printed. **Checkpoint #1 passed**.

No commit in this task (all artifacts are in /tmp, not in repo).

---

## Task 2: Phase 1 — Delete vancouver/mdpi fixtures + tests (chore(remove))

**Goal:** Remove the 4 affected paths from working tree, verify tests still pass on the reduced set, commit, push.

**Files:**
- Delete: `tests/fixtures/vancouver_24refs/` (entire directory)
- Delete: `tests/fixtures/mdpi_149refs/` (entire directory)
- Delete: `tests/test_integration_vancouver_24refs.py`
- Delete: `tests/test_integration_149refs.py`

- [ ] **Step 1: Verify current test count baseline**

```bash
python3 -m pytest tests/ -q 2>&1 | tail -3
```

Expected: `101 passed, 1 skipped`. If different, stop and investigate.

- [ ] **Step 2: Delete the 4 paths**

```bash
git rm -r tests/fixtures/vancouver_24refs/
git rm -r tests/fixtures/mdpi_149refs/
git rm tests/test_integration_vancouver_24refs.py
git rm tests/test_integration_149refs.py
git status --short
```

Expected: 13+ files staged for deletion (5 in vancouver_24refs + 6 in mdpi_149refs + 2 test files).

- [ ] **Step 3: Run pytest to confirm reduced test count is green**

```bash
python3 -m pytest tests/ -q 2>&1 | tail -5
```

Expected: ~92 passed, 1 skipped (101 − 5 vancouver tests − 4 mdpi tests). Exact count may differ slightly. CRITICAL: no FAILures. If any other test (e.g., `test_overrides_contract.py`, `test_journal_audit.py`) fails, stop — it implies cross-fixture coupling that must be investigated.

- [ ] **Step 4: Record the new baseline test count**

```bash
NEW_TEST_COUNT=$(python3 -m pytest tests/ -q 2>&1 | grep -oE '[0-9]+ passed' | head -1)
echo "Post-deletion test count: $NEW_TEST_COUNT" > /tmp/day23_post_delete_test_count.txt
cat /tmp/day23_post_delete_test_count.txt
```

Expected: something like `Post-deletion test count: 92 passed`. Record exact number for Phase 5 reconciliation.

- [ ] **Step 5: Commit**

```bash
git commit -m "$(cat <<'EOF'
chore(remove): delete vancouver_24refs + mdpi_149refs fixtures and tests (Day23 Phase 1)

Day19 Public 切替後に判明した著作権・査読守秘義務上の懸念に対する
remediation の Phase 1. 該当 2 fixture と対応 integration test を
削除. 続く Phase 2 (filter-repo) で git history から完全除去予定.

削除内容:
  - tests/fixtures/vancouver_24refs/ (5 files、Day9 (Z) commit fe38298
    で導入、OneDrive 上の 参照.docx 由来、Vancouver style 24 refs)
  - tests/fixtures/mdpi_149refs/ (6 files、commit a0bba56 で導入、
    README 未作成で出典記述ゼロ、149 ref corpus)
  - tests/test_integration_vancouver_24refs.py
  - tests/test_integration_149refs.py

test 影響: 101 passed / 1 skipped → ~92 passed / 1 skipped (regression なし、
削除した fixture に依存しない tests は全て pass 継続).

次 commit 後に Phase 2 (filter-repo) で git history からも完全消去.
新 fixture (PMC OA CC BY 4.0 由来) は Phase 5 で追加予定.

spec: docs/superpowers/specs/2026-05-24-day23-fixture-remediation-design.md
plan: docs/superpowers/plans/2026-05-24-day23-fixture-remediation.md

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 6: Push to origin/main (Private repo)**

```bash
git push origin main
git log --oneline -3
```

Expected: push succeeds. Commits visible: this commit, plan commit, spec commit. **Checkpoint #2 passed**.

---

## Task 3: Phase 2 — filter-repo (DESTRUCTIVE, requires explicit user approval — Gate #A)

**Goal:** Strip `tests/fixtures/vancouver_24refs` and `tests/fixtures/mdpi_149refs` from ALL git history.

**⚠️ DESTRUCTIVE OPERATION**: This rewrites all commits that touched the affected paths. All SHAs from those commits onward change. Cannot be undone without restoring from backup. **Pause here and confirm with user before executing Step 1.**

**Files:**
- Modify: `.git/` (entirely rewritten by filter-repo)

- [ ] **Step 1: Confirm user approval for filter-repo execution (Gate #A)**

State explicitly to the user:

> "About to run `git filter-repo --path tests/fixtures/vancouver_24refs --path tests/fixtures/mdpi_149refs --invert-paths --force`. This rewrites ALL git history, removing the two paths from every commit. Cannot be undone except from the /tmp backup. Proceed?"

Wait for explicit "yes" or equivalent. If user says no or wants to revisit, stop and report back.

- [ ] **Step 2: Run filter-repo**

```bash
cd /Users/katayamahideki/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver
git filter-repo \
  --path tests/fixtures/vancouver_24refs \
  --path tests/fixtures/mdpi_149refs \
  --invert-paths \
  --force
```

Expected output: "Parsed ... commits", "New history written", "Done". Possibly some warnings about parsed objects.

If filter-repo fails (e.g., not on $PATH), check Step 5 of Task 1 (install via brew) and re-run.

- [ ] **Step 3: Verify both paths are absent from all history (4 ways)**

```bash
echo "=== git log check ==="
git log --all --oneline -- tests/fixtures/vancouver_24refs
git log --all --oneline -- tests/fixtures/mdpi_149refs
echo "=== git rev-list grep check ==="
git rev-list --all --objects | grep -c 'tests/fixtures/vancouver_24refs' || echo "0 (good)"
git rev-list --all --objects | grep -c 'tests/fixtures/mdpi_149refs' || echo "0 (good)"
echo "=== .git size ==="
du -sh .git
```

Expected:
- Both `git log` commands print nothing (empty)
- Both grep counts = 0
- `.git` size decreased noticeably (vancouver ~30KB + mdpi ~1MB stripped, plus pack rebuild)

If any check fails (paths still present in history), STOP — restore from backup (Step 4 below) and investigate.

- [ ] **Step 4 (only if Step 3 failed): Restore from backup**

```bash
rm -rf /Users/katayamahideki/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver
cp -R /tmp/pubmed-reference-resolver_backup_20260524 \
      /Users/katayamahideki/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver
cd /Users/katayamahideki/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver
md5 .git/HEAD
diff /tmp/day23_backup_md5.txt <(md5 /tmp/pubmed-reference-resolver_backup_20260524/.git/HEAD | awk '{print $4}')
```

Then report BLOCKED with the filter-repo error message. Do NOT proceed to Phase 3.

- [ ] **Step 5: Snapshot new SHAs (for Phase 4 reference)**

```bash
git log --oneline -20 > /tmp/day23_post_rewrite_log.txt
# Map old → new SHA for each Day22 commit (10 commits)
for subject_pattern in \
  "chore(security): suppress 4 recursive false positives" \
  "docs(spec): add brainstorming spec for Rule 3 NLM" \
  "docs(plan): add implementation plan for Rule 3 NLM" \
  "test(nlm): add failing test_fetch_json_uses_certifi" \
  "fix(nlm): inject certifi SSL context" \
  "docs(nlm): update module docstring after certifi" \
  "test(fixtures): regenerate cell + apa baselines" \
  "docs(tests): update integration test docstrings" \
  "docs(sessions): archive day22 Rule 3 NLM SSL fix" \
  "docs(sessions): fix 3 factual errors in Day22 archive"; do
  new_sha=$(git log --all --format="%H %s" | grep -F "$subject_pattern" | head -1 | awk '{print $1}')
  echo "$subject_pattern → $new_sha"
done > /tmp/day23_sha_remap.txt
cat /tmp/day23_sha_remap.txt
```

Expected: 10 new SHAs printed, one per Day22 commit pattern.

- [ ] **Step 6: Snapshot Day19 SECRET_SCAN_REPORT new SHA**

```bash
NEW_DAY19_SHA=$(git log --all --grep="docs(security): add Day19 pre-public secret scan report" --pretty=%H | head -1)
echo "$NEW_DAY19_SHA" > /tmp/day23_new_day19_sha.txt
cat /tmp/day23_new_day19_sha.txt
```

Expected: 40-char SHA printed. **Checkpoint #3 passed**.

---

## Task 4: Phase 3 — Force push + tag/release re-create (DESTRUCTIVE, Gate #B)

**Goal:** Push the rewritten history to GitHub, delete + re-create v0.1.0 tag and Release.

**⚠️ DESTRUCTIVE OPERATIONS** (CLAUDE.md §7.2.2 forbids without explicit approval):
- `git push --force origin main`
- `git push origin :refs/tags/v0.1.0` (tag deletion)
- `gh release delete v0.1.0`

- [ ] **Step 1: Confirm user approval for force push (Gate #B)**

State explicitly to the user:

> "About to execute 3 destructive operations: (1) `git push --force origin main` to overwrite GitHub history with the filter-repo result, (2) `git push origin :refs/tags/v0.1.0` to delete the old v0.1.0 tag on GitHub, (3) `gh release delete v0.1.0 --yes` to delete the old Release. Then re-create tag + Release on the new SHA. Proceed?"

Wait for explicit "yes".

- [ ] **Step 2: Re-add origin remote (filter-repo removes it for safety)**

```bash
git remote -v  # should be empty
git remote add origin https://github.com/hikataya01-netizen/pubmed-reference-resolver.git
git remote -v  # should now list origin
```

- [ ] **Step 3: Force push main**

```bash
git push --force origin main
```

Expected: push succeeds. If rejected with "branch protection rule violation", the repo's branch protection on `main` needs to be temporarily disabled — but as verified in pre-flight, Private repos on free GitHub plan don't have branch protection. If still rejected, investigate.

- [ ] **Step 4: Delete old v0.1.0 tag (remote + local)**

```bash
git push origin :refs/tags/v0.1.0
git tag -d v0.1.0
git tag | grep v0.1.0 || echo "tag deleted locally and remotely (good)"
```

Expected: both deletions succeed.

- [ ] **Step 5: Re-create v0.1.0 tag on new SHA**

```bash
# The v0.1.0 tag originally pointed to commit "docs(changelog): add Day20 entry"
# (Day21 Phase 1 commit, original SHA 568a17c). Find the new SHA after filter-repo:
NEW_V010_SHA=$(git log --all --grep="docs(changelog): add Day20 entry" --pretty=%H | head -1)
echo "New v0.1.0 SHA: $NEW_V010_SHA"

# Re-create as annotated tag, reusing the saved release notes as tag message
git tag -a v0.1.0 "$NEW_V010_SHA" -F /tmp/v010_release_notes_day23_restore.md
git push origin v0.1.0

# Verify
git cat-file -t v0.1.0  # should print "tag" (annotated)
gh api repos/hikataya01-netizen/pubmed-reference-resolver/git/refs/tags/v0.1.0 --jq '.object.sha'
```

Expected: tag type = `tag` (annotated). GitHub refs match local.

- [ ] **Step 6: Delete + re-create GitHub Release**

```bash
gh release delete v0.1.0 --yes
gh release create v0.1.0 \
  --notes-file /tmp/v010_release_notes_day23_restore.md \
  --title "$(cat /tmp/v010_release_title.txt)"
gh release view v0.1.0 --json tagName,isDraft,name --jq .
```

Expected: release JSON shows `tagName: v0.1.0`, `isDraft: false`, name matches title saved in Phase 0.

- [ ] **Step 7: Verify GitHub state matches local state**

```bash
LOCAL_MAIN=$(git rev-parse HEAD)
REMOTE_MAIN=$(gh api repos/hikataya01-netizen/pubmed-reference-resolver/commits/main --jq .sha)
echo "Local:  $LOCAL_MAIN"
echo "Remote: $REMOTE_MAIN"
test "$LOCAL_MAIN" = "$REMOTE_MAIN" && echo "MATCH" || echo "MISMATCH"
```

Expected: MATCH. **Checkpoint #4 passed**.

No git commit in this task (operations are push/tag/release, not local commits).

---

## Task 5: Phase 4a — Refresh .gitleaksignore Day19 fingerprints

**Goal:** Update the 4 Day19 SECRET_SCAN_REPORT fingerprints in `.gitleaksignore` to use the post-filter-repo SHA.

**Files:**
- Modify: `.gitleaksignore` (4 lines updated, old `52320b6...` → new SHA)

- [ ] **Step 1: Get the new Day19 SHA**

```bash
NEW_DAY19_SHA=$(cat /tmp/day23_new_day19_sha.txt)
echo "Replacing old SHA 52320b6d8ad166c4d1ef31ce5c0e608076aad527 with: $NEW_DAY19_SHA"
```

Expected: 40-char SHA printed (from Task 3 Step 6).

- [ ] **Step 2: Update .gitleaksignore via sed**

```bash
sed -i.bak "s/52320b6d8ad166c4d1ef31ce5c0e608076aad527/$NEW_DAY19_SHA/g" .gitleaksignore
diff .gitleaksignore.bak .gitleaksignore
rm .gitleaksignore.bak
```

Expected: diff shows exactly 4 lines changed (the four Day19 fingerprint lines 24-27 area).

- [ ] **Step 3: Re-run gitleaks to confirm clean**

```bash
gitleaks detect --no-banner --redact 2>&1 | tail -3
```

Expected: `no leaks found`. If leaks found, the SHA replacement didn't work — investigate and redo Step 2.

- [ ] **Step 4: Commit**

```bash
git add .gitleaksignore
git commit -m "$(cat <<'EOF'
chore(security): refresh Day19 fingerprints after filter-repo SHA invalidation (Day23 Phase 4)

Phase 2 (filter-repo) で vancouver/mdpi fixture を全 history から strip
した結果、Day19 SECRET_SCAN_REPORT (commit) の SHA が
52320b6d8ad166c4d1ef31ce5c0e608076aad527 から新 SHA に変化.
.gitleaksignore の Day19 fingerprint 4 件を新 SHA に書換.

Day8/Day18 由来の 3 fingerprint (d49dc58, c9dce0b, 8d8c7e3) は
vancouver/mdpi 導入前 commit なので SHA 不変、修正不要.

gitleaks 再 scan: no leaks found (継続).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

- [ ] **Step 5: Verify**

```bash
gitleaks detect --no-banner --redact 2>&1 | tail -3
grep -c "$(cat /tmp/day23_new_day19_sha.txt)" .gitleaksignore
```

Expected: `no leaks found` + count = 4 (the 4 new fingerprint lines).

---

## Task 6: Phase 4b — Update Day22 archive SHA table

**Goal:** Replace the 10 old Day22 SHAs in `docs/sessions/day22/README.md` + `DAY22_LESSONS_LEARNED.md` with their new post-filter-repo SHAs.

**Files:**
- Modify: `docs/sessions/day22/README.md`
- Modify: `docs/sessions/day22/DAY22_LESSONS_LEARNED.md`

- [ ] **Step 1: Build SHA remap dictionary from `/tmp/day23_sha_remap.txt`**

```bash
cat /tmp/day23_sha_remap.txt
```

Expected: 10 lines mapping subject patterns to new SHAs (from Task 3 Step 5).

- [ ] **Step 2: Build old→new SHA map**

For each of the 10 old SHAs (c0993f0, af9e55a, d797307, 301eb9e, 685a600, f512562, c6e951c, 87d054f, 7d05830, 2ddf6cd), find the new SHA (short form, 7 chars) by matching the commit subject pattern.

```bash
declare -A SHA_MAP
SHA_MAP[c0993f0]=$(git log --all --grep="chore(security): suppress 4 recursive false positives" --pretty=%h | head -1)
SHA_MAP[af9e55a]=$(git log --all --grep="docs(spec): add brainstorming spec for Rule 3 NLM" --pretty=%h | head -1)
SHA_MAP[d797307]=$(git log --all --grep="docs(plan): add implementation plan for Rule 3 NLM" --pretty=%h | head -1)
SHA_MAP[301eb9e]=$(git log --all --grep="test(nlm): add failing test_fetch_json_uses_certifi" --pretty=%h | head -1)
SHA_MAP[685a600]=$(git log --all --grep="fix(nlm): inject certifi SSL context" --pretty=%h | head -1)
SHA_MAP[f512562]=$(git log --all --grep="docs(nlm): update module docstring after certifi" --pretty=%h | head -1)
SHA_MAP[c6e951c]=$(git log --all --grep="test(fixtures): regenerate cell + apa baselines" --pretty=%h | head -1)
SHA_MAP[87d054f]=$(git log --all --grep="docs(tests): update integration test docstrings" --pretty=%h | head -1)
SHA_MAP[7d05830]=$(git log --all --grep="docs(sessions): archive day22 Rule 3 NLM SSL fix" --pretty=%h | head -1)
SHA_MAP[2ddf6cd]=$(git log --all --grep="docs(sessions): fix 3 factual errors in Day22 archive" --pretty=%h | head -1)

for old in c0993f0 af9e55a d797307 301eb9e 685a600 f512562 c6e951c 87d054f 7d05830 2ddf6cd; do
  echo "$old → ${SHA_MAP[$old]}"
done
```

Expected: 10 old→new mappings printed. Each new SHA is a 7-char short form.

- [ ] **Step 3: Apply sed replacements to both Day22 archive files**

```bash
for old in c0993f0 af9e55a d797307 301eb9e 685a600 f512562 c6e951c 87d054f 7d05830 2ddf6cd; do
  new="${SHA_MAP[$old]}"
  sed -i.bak "s/\`$old\`/\`$new\`/g" docs/sessions/day22/README.md docs/sessions/day22/DAY22_LESSONS_LEARNED.md
done
rm docs/sessions/day22/*.bak
```

- [ ] **Step 4: Verify no old SHAs remain**

```bash
grep -E "c0993f0|af9e55a|d797307|301eb9e|685a600|f512562|c6e951c|87d054f|7d05830|2ddf6cd" \
  docs/sessions/day22/README.md docs/sessions/day22/DAY22_LESSONS_LEARNED.md
```

Expected: NO output (zero matches). If matches found, the sed didn't replace them — check escaping and re-run.

- [ ] **Step 5: Commit**

```bash
git add docs/sessions/day22/README.md docs/sessions/day22/DAY22_LESSONS_LEARNED.md
git commit -m "$(cat <<'EOF'
docs(sessions): refresh Day22 archive SHA table after filter-repo (Day23 Phase 4)

Phase 2 (filter-repo) で vancouver/mdpi を strip した結果、Day22 の
10 commit SHA (c0993f0, af9e55a, d797307, 301eb9e, 685a600, f512562,
c6e951c, 87d054f, 7d05830, 2ddf6cd) が全て新 SHA に変化.

docs/sessions/day22/README.md の commit table と DAY22_LESSONS_LEARNED.md
の §3 commit chain に記載された 10 SHA を新 SHA で書換 (sed 一括置換).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

---

## Task 7: Phase 4c — Update memory file SHAs (if applicable)

**Goal:** If any memory files in `~/.claude/projects/.../memory/` contain old Day22 SHAs, replace them.

**Files:**
- Modify (conditional): `~/.claude/projects/-Users-katayamahideki-Desktop-Claude-------reference--pubmed-reference-resolver/memory/project_mdpi_integration.md` (likely contains `1dbf9d7` or other invalidated SHA)

- [ ] **Step 1: Grep memory files for any old SHAs**

```bash
MEMORY_DIR=~/.claude/projects/-Users-katayamahideki-Desktop-Claude-------reference--pubmed-reference-resolver/memory
grep -rln -E "1dbf9d7|c0993f0|af9e55a|d797307|301eb9e|685a600|f512562|c6e951c|87d054f|7d05830|2ddf6cd|52320b6d8ad166c4d1ef31ce5c0e608076aad527" \
  "$MEMORY_DIR" 2>/dev/null
```

Expected: list of memory files containing old SHAs. Likely candidates: `project_mdpi_integration.md`.

- [ ] **Step 2: If matches found, update each file**

For each file in Step 1's output, view the matching lines and decide what to do:
- If the old SHA is purely historical context (e.g., "Step 5 完了 (HEAD 1dbf9d7)"), update to new equivalent SHA via grep + sed
- If the file references `1dbf9d7` which is from the feature/mdpi-fast-path branch (pre-Day22), look up that subject and find new SHA
- If no clean mapping exists, replace with note "SHA invalidated by Day23 filter-repo (2026-05-24)"

```bash
# Example for project_mdpi_integration.md (adapt to actuals)
OLD_SHA="1dbf9d7"
# Find subject for this old SHA — it was a feature branch step 5 commit
# If no longer findable in git log, annotate with the Day23 note
NEW_SHA=$(git log --all --grep="Step 5 OR feature/mdpi-fast-path Step 5" --pretty=%h 2>/dev/null | head -1)
if [ -z "$NEW_SHA" ]; then
  NEW_SHA="(invalidated-day23-filter-repo)"
fi
sed -i.bak "s/$OLD_SHA/$NEW_SHA/g" "$MEMORY_DIR/project_mdpi_integration.md"
diff "$MEMORY_DIR/project_mdpi_integration.md.bak" "$MEMORY_DIR/project_mdpi_integration.md"
rm "$MEMORY_DIR/project_mdpi_integration.md.bak"
```

- [ ] **Step 3: Verify**

```bash
grep -E "1dbf9d7|c0993f0|af9e55a|d797307|301eb9e|685a600|f512562|c6e951c|87d054f|7d05830|2ddf6cd|52320b6d8ad166c4d1ef31ce5c0e608076aad527" \
  "$MEMORY_DIR"/*.md
```

Expected: no matches (or only intentional annotations).

- [ ] **Step 4: Commit (only if memory files were inside repo — they are NOT)**

Memory files live in `~/.claude/projects/.../memory/` which is OUTSIDE the repo. No git commit needed.

Mark this task as complete only after the grep in Step 3 returns clean.

**Note:** if Step 1 returned no matches, this entire task is a no-op and you can skip immediately to Task 8.

---

## Task 8: Phase 5a — PMC candidate search + user selection

**Goal:** Find 3-5 PMC OA candidates for each of Vancouver-style and MDPI-style replacement fixtures, present to user, get selection.

**Files:**
- Create (temp): `/tmp/day23_vancouver_candidates.md`
- Create (temp): `/tmp/day23_mdpi_candidates.md`
- Create (temp): `/tmp/day23_user_selection.txt`

- [ ] **Step 1: Search PMC for Vancouver-style candidates**

Vancouver-style criteria: numbered references, medical domain, PMC OA CC BY 4.0, ~20-30 refs.

Suggested approach (using NCBI E-utilities directly via curl or via the `paper-search` skill if available):

```bash
# Approach A: paper-search skill (if available, scoped to palliative care / supportive care / oncology)
# Approach B: direct NCBI E-utilities

# Example NCBI esearch query (palliative care domain, OA, recent):
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&term=palliative+care%5BMeSH%5D+AND+open+access%5Bfilter%5D+AND+2024%3A2026%5Bpdat%5D&retmax=20&retmode=json" \
  | python3 -m json.tool
```

For each PMC ID returned, run efetch to get JATS XML and count refs:

```bash
PMC_ID=PMC12345678  # example
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id=$PMC_ID&rettype=xml" \
  | python3 -c "
import sys, xml.etree.ElementTree as ET
tree = ET.parse(sys.stdin)
refs = tree.findall('.//ref')
print(f'Total refs: {len(refs)}')
# Find license info
license_el = tree.find('.//license/license-p') or tree.find('.//license')
if license_el is not None:
    print(f'License: {ET.tostring(license_el, encoding=\"unicode\")[:200]}')
"
```

Filter for: 20-30 refs, CC BY 4.0 license.

Build `/tmp/day23_vancouver_candidates.md` with this format:

```markdown
# Vancouver replacement candidates

| # | PMC ID | DOI | Journal | Year | Topic | refs | License | Title (truncated) |
|:---|:---|:---|:---|:---:|:---|:---:|:---|:---|
| V1 | PMC..... | 10.xxxx | BMC Palliat Care | 2025 | 緩和 | 23 | CC BY 4.0 | "..." |
| V2 | PMC..... | 10.xxxx | Supportive Care in Cancer | 2024 | 支持療法 | 27 | CC BY 4.0 | "..." |
| ... |
```

- [ ] **Step 2: Search PMC for MDPI-style candidates**

MDPI criteria: MDPI publisher journals (Cancers, Healthcare, Nutrients, IJERPH, Sensors), 50-150 refs, review papers preferred.

```bash
# Example: MDPI Cancers review papers
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&term=cancers%5Bjournal%5D+AND+review%5Bpt%5D+AND+open+access%5Bfilter%5D+AND+2024%3A2026%5Bpdat%5D&retmax=30&retmode=json" \
  | python3 -m json.tool
```

Filter for: 50-150 refs, CC BY 4.0.

Build `/tmp/day23_mdpi_candidates.md` with the same table format.

- [ ] **Step 3: Present both candidate lists to user**

Display both /tmp files via Read tool and announce to user:

> "PMC OA replacement candidates ready: 3-5 Vancouver-style and 3-5 MDPI-style. Please review `/tmp/day23_vancouver_candidates.md` and `/tmp/day23_mdpi_candidates.md` and select 1 Vancouver + 1 MDPI (e.g., V2 + M3). Respond with the IDs."

Wait for user selection.

- [ ] **Step 4: Record user selection**

```bash
# After user responds (e.g., "V2 + M3"), save
echo "Selected Vancouver: PMC........(V2)" > /tmp/day23_user_selection.txt
echo "Selected MDPI: PMC........(M3)" >> /tmp/day23_user_selection.txt
cat /tmp/day23_user_selection.txt
```

No git commit in this task (artifacts in /tmp).

---

## Task 9: Phase 5b — Build new fixtures (Vancouver + MDPI replacement)

**Goal:** Create `tools/build_vancouver_replacement_fixture.py` + `tools/build_mdpi_replacement_fixture.py`, run them to generate input docx, then run `main.py` to generate baseline JSON/report files.

**Files:**
- Create: `tools/build_vancouver_replacement_fixture.py` (based on `build_apa_fixture.py` template)
- Create: `tools/build_mdpi_replacement_fixture.py` (same template)
- Create: `tests/fixtures/vancouver_<N>refs/` with `input_References.docx`, `expected_phase1_intermediate.json`, `baseline_phase3_resolved.json`, `baseline_report.md`, `baseline_three_class_classification.json`, `README.md`
- Create: `tests/fixtures/mdpi_<N>refs/` with the same 6 files

- [ ] **Step 1: Read the apa fixture build tool as template**

```bash
wc -l tools/build_apa_fixture.py
head -50 tools/build_apa_fixture.py
```

Expected: ~150-300 lines. Identify the PMC fetch + JATS parse + python-docx output sections.

- [ ] **Step 2: Create build_vancouver_replacement_fixture.py**

Copy `tools/build_apa_fixture.py` to `tools/build_vancouver_replacement_fixture.py`. Modify:
- Source PMC IDs: replace with the user-selected Vancouver paper's PMC ID
- Output path: `tests/fixtures/vancouver_<N>refs/input_References.docx`
- Numbering style: Vancouver (numbered list, e.g., `1. Smith JA, et al. ...`)
- Adjust ref extraction logic if Vancouver formatting differs from APA

```bash
cp tools/build_apa_fixture.py tools/build_vancouver_replacement_fixture.py
# Edit the new file: change PMC IDs, output path, numbering style
```

(Specifics depend on actual user-selected paper — engineer should read build_apa_fixture.py and adapt accordingly.)

- [ ] **Step 3: Run build_vancouver_replacement_fixture.py**

```bash
mkdir -p tests/fixtures/vancouver_<N>refs/  # replace <N> with actual ref count
python3 tools/build_vancouver_replacement_fixture.py
ls -la tests/fixtures/vancouver_<N>refs/input_References.docx
```

Expected: docx file generated, size > 0.

- [ ] **Step 4: Generate Vancouver Phase 1 baseline (parser only)**

```bash
set -a; source skill_package/.env; set +a
python3 main.py tests/fixtures/vancouver_<N>refs/input_References.docx \
  --output-dir /tmp/vancouver_replacement_day23 --phase 1
cp /tmp/vancouver_replacement_day23/phase1_intermediate.json \
   tests/fixtures/vancouver_<N>refs/expected_phase1_intermediate.json
```

Expected: phase1_intermediate.json generated with N refs parsed.

- [ ] **Step 5: Generate Vancouver Phase 3 + Phase 4 baseline (LLM + PubMed + synthesize)**

```bash
python3 main.py tests/fixtures/vancouver_<N>refs/input_References.docx \
  --output-dir /tmp/vancouver_replacement_day23
cp /tmp/vancouver_replacement_day23/phase3_resolved.json \
   tests/fixtures/vancouver_<N>refs/baseline_phase3_resolved.json
cp /tmp/vancouver_replacement_day23/report.md \
   tests/fixtures/vancouver_<N>refs/baseline_report.md
cp /tmp/vancouver_replacement_day23/three_class_classification.json \
   tests/fixtures/vancouver_<N>refs/baseline_three_class_classification.json
```

Expected: 3 files copied. LLM cost ~$0.5 for ~24 refs.

- [ ] **Step 6: Create Vancouver README.md**

Use `tests/fixtures/apa_45refs/README.md` as template. Fill in:
- Source PMC ID, DOI, Journal, Year, License (CC BY 4.0)
- Title (full)
- Ref count actual
- Day23 origin context
- File listing with sizes

```bash
# Copy template and edit
cp tests/fixtures/apa_45refs/README.md tests/fixtures/vancouver_<N>refs/README.md
# Manually edit to reflect the new fixture's actual source
```

- [ ] **Step 7: Repeat Steps 2-6 for MDPI replacement**

```bash
cp tools/build_apa_fixture.py tools/build_mdpi_replacement_fixture.py
# Edit for MDPI paper's PMC ID, output path tests/fixtures/mdpi_<N>refs/

mkdir -p tests/fixtures/mdpi_<N>refs/
python3 tools/build_mdpi_replacement_fixture.py

python3 main.py tests/fixtures/mdpi_<N>refs/input_References.docx \
  --output-dir /tmp/mdpi_replacement_day23 --phase 1
cp /tmp/mdpi_replacement_day23/phase1_intermediate.json \
   tests/fixtures/mdpi_<N>refs/expected_phase1_intermediate.json

python3 main.py tests/fixtures/mdpi_<N>refs/input_References.docx \
  --output-dir /tmp/mdpi_replacement_day23
cp /tmp/mdpi_replacement_day23/phase3_resolved.json \
   tests/fixtures/mdpi_<N>refs/baseline_phase3_resolved.json
cp /tmp/mdpi_replacement_day23/report.md \
   tests/fixtures/mdpi_<N>refs/baseline_report.md
cp /tmp/mdpi_replacement_day23/three_class_classification.json \
   tests/fixtures/mdpi_<N>refs/baseline_three_class_classification.json

cp tests/fixtures/apa_45refs/README.md tests/fixtures/mdpi_<N>refs/README.md
# Edit
```

LLM cost ~$1.5-3 for ~80-149 refs.

- [ ] **Step 8: Commit build tools + new fixtures**

```bash
git add tools/build_vancouver_replacement_fixture.py \
        tools/build_mdpi_replacement_fixture.py \
        tests/fixtures/vancouver_<N>refs/ \
        tests/fixtures/mdpi_<N>refs/
git status --short
git commit -m "$(cat <<'EOF'
feat(fixtures): add Vancouver + MDPI PMC OA replacement fixtures (Day23 Phase 5)

Day23 で削除した vancouver_24refs + mdpi_149refs の代替として、PMC OA
CC BY 4.0 由来の 2 fixture を新規追加.

新 fixture:
  - tests/fixtures/vancouver_<N>refs/ (PMC <id>, <Journal>, Vancouver
    style, <N> refs, CC BY 4.0)
  - tests/fixtures/mdpi_<N>refs/ (PMC <id>, <MDPI Journal>, MDPI style,
    <N> refs, CC BY 4.0)

各 fixture は input_References.docx + expected_phase1_intermediate.json
+ baseline_{phase3_resolved.json, report.md, three_class_classification.json}
+ README.md (出典明示) の 6 ファイル構成 (apa_45refs / cell_45refs と
同 pattern).

新 tools:
  - tools/build_vancouver_replacement_fixture.py
  - tools/build_mdpi_replacement_fixture.py
  (いずれも tools/build_apa_fixture.py の template ベース)

LLM cost: ~$2-3.5 (baseline 生成).

次 commit で integration test (apa/cell 8-test template) を追加予定.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

(Replace `<N>` placeholders in the commit message body with actual ref counts.)

---

## Task 10: Phase 5c — Add integration tests for new fixtures

**Goal:** Create `tests/test_integration_vancouver_<N>refs.py` + `tests/test_integration_mdpi_<N>refs.py` based on the apa/cell 8-test template.

**Files:**
- Create: `tests/test_integration_vancouver_<N>refs.py` (copy of apa, ~270 lines)
- Create: `tests/test_integration_mdpi_<N>refs.py` (copy of apa, ~270 lines)

- [ ] **Step 1: Read apa integration test as template**

```bash
wc -l tests/test_integration_apa_45refs.py
```

Expected: ~270-320 lines. The 8-test pattern includes phase1 deterministic, phase3 baseline, report baseline, three-class distribution.

- [ ] **Step 2: Create Vancouver integration test**

```bash
cp tests/test_integration_apa_45refs.py tests/test_integration_vancouver_<N>refs.py
# Edit: replace "apa_45refs" with "vancouver_<N>refs" throughout
# Adjust EXPECTED_THREE_CLASS_DISTRIBUTION to match actual measured values from baseline
```

Use sed for the simple path replacement:
```bash
sed -i.bak "s|apa_45refs|vancouver_<N>refs|g" tests/test_integration_vancouver_<N>refs.py
rm tests/test_integration_vancouver_<N>refs.py.bak
```

Then manually edit:
- Test name suffix: `test_apa_*` → `test_vancouver_*`
- Docstrings to reference Vancouver style
- `EXPECTED_THREE_CLASS_DISTRIBUTION` literal to match `tests/fixtures/vancouver_<N>refs/baseline_three_class_classification.json` actuals (read the JSON and count)

```bash
# Get actual distribution
python3 -c "
import json
data = json.loads(open('tests/fixtures/vancouver_<N>refs/baseline_three_class_classification.json').read())
dist = {'A': 0, 'B': 0, 'C': 0, 'unknown': 0}
for c in data:
    cls = c.get('class', 'unknown')
    dist[cls] = dist.get(cls, 0) + 1
print('Vancouver:', dist)
"
# Use the printed numbers to update EXPECTED_THREE_CLASS_DISTRIBUTION
```

- [ ] **Step 3: Run Vancouver integration test**

```bash
python3 -m pytest tests/test_integration_vancouver_<N>refs.py -v 2>&1 | tail -15
```

Expected: 8 tests pass. If a test fails with EXPECTED_* mismatch, update the EXPECTED_* literal to match actual baseline.

- [ ] **Step 4: Create MDPI integration test (same procedure as Steps 2-3)**

```bash
cp tests/test_integration_apa_45refs.py tests/test_integration_mdpi_<N>refs.py
sed -i.bak "s|apa_45refs|mdpi_<N>refs|g" tests/test_integration_mdpi_<N>refs.py
rm tests/test_integration_mdpi_<N>refs.py.bak
# Edit: test name suffix, docstrings, EXPECTED_THREE_CLASS_DISTRIBUTION to match MDPI baseline
python3 -m pytest tests/test_integration_mdpi_<N>refs.py -v 2>&1 | tail -15
```

Expected: 8 tests pass.

- [ ] **Step 5: Run full test suite**

```bash
python3 -m pytest tests/ -q 2>&1 | tail -5
```

Expected: ~108 passed (92 from Phase 1 + 8 vancouver + 8 mdpi), 1 skipped.

- [ ] **Step 6: Commit**

```bash
git add tests/test_integration_vancouver_<N>refs.py tests/test_integration_mdpi_<N>refs.py
git commit -m "$(cat <<'EOF'
test(integration): add 8-test integration suite for new Vancouver + MDPI fixtures (Day23 Phase 5)

Day23 で追加した新 fixture (vancouver_<N>refs + mdpi_<N>refs) 用に
apa/cell 8-test template を流用した integration test を追加.

各 test file の構成 (apa/cell と同 pattern):
  - Test 1: 全 refs が LLM path にルーティング (Vancouver Veto 検証)
  - Test 2-3: phase1 deterministic (parser-only) byte match
  - Test 4-5: phase3 + report baseline (document-of-record)
  - Test 6-7: style-specific marker 検出 (Vancouver: numbered, MDPI: MDPI signal)
  - Test 8: three-class classification distribution (実測値で EXPECTED 固定)

実測 three-class distribution:
  - vancouver_<N>refs: A=<X>, B=<X>, C=<X>, unknown=<X>
  - mdpi_<N>refs: A=<X>, B=<X>, C=<X>, unknown=<X>

全 tests: ~108 passed, 1 skipped (元 92 + 新 vancouver 8 + 新 mdpi 8).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

(Replace `<N>` and `<X>` placeholders with actuals.)

---

## Task 11: Phase 6 — Re-public + Day23 archive

**Goal:** Switch repo back to public, verify CI green and v0.1.0 release URL accessible, write Day23 archive.

**Files:**
- Create: `docs/sessions/day23/README.md`
- Create: `docs/sessions/day23/DAY23_LESSONS_LEARNED.md`

- [ ] **Step 1: Final pre-public verification**

```bash
# Tests green
python3 -m pytest tests/ -q 2>&1 | tail -3

# gitleaks clean
gitleaks detect --no-banner --redact 2>&1 | tail -3

# Both deleted paths absent
git log --all --oneline -- tests/fixtures/vancouver_24refs
git log --all --oneline -- tests/fixtures/mdpi_149refs

# v0.1.0 tag + release still exist on private repo
gh release view v0.1.0 --json tagName,isDraft

# Local matches remote
test "$(git rev-parse HEAD)" = "$(gh api repos/hikataya01-netizen/pubmed-reference-resolver/commits/main --jq .sha)" \
  && echo "MATCH" || echo "MISMATCH"
```

Expected: tests ~108 passed, gitleaks clean, both git log empty, release v0.1.0 exists, MATCH. **If any check fails, do NOT proceed to public.**

- [ ] **Step 2: Switch repo to public**

```bash
gh repo edit hikataya01-netizen/pubmed-reference-resolver --visibility public --accept-visibility-change-consequences
gh repo view hikataya01-netizen/pubmed-reference-resolver --json visibility,isPrivate
```

Expected: `{"isPrivate": false, "visibility": "PUBLIC"}`.

- [ ] **Step 3: Verify v0.1.0 release URL accessible**

```bash
sleep 5  # let GitHub propagate visibility change
curl -sI "https://github.com/hikataya01-netizen/pubmed-reference-resolver/releases/tag/v0.1.0" | head -3
```

Expected: `HTTP/2 200`. (or 301 redirect to a 200, depending on GitHub).

- [ ] **Step 4: Verify CI passes on new SHA**

```bash
sleep 30  # let GitHub Actions trigger
gh run list --limit 3 --json conclusion,name,headSha,status
```

Expected: most recent run for current HEAD shows `conclusion: success, status: completed`. If `in_progress`, wait and re-check. If failed, investigate.

- [ ] **Step 5: Create Day23 README.md (archive index)**

Create `docs/sessions/day23/README.md` with the structure below. Substitute actual values (test counts, new fixture names, new SHAs from this session).

```markdown
# Day23 Session Archive (2026-05-24)

## 概要

Day23 セッションは Day22 末セッションで判明した「vancouver_24refs +
mdpi_149refs の 2 fixture が査読由来 (input_References.docx が査読
manuscript 起源) で著作権・査読守秘義務上の懸念がある」事象への
remediation セッション.

Pattern C (Private + filter-repo + force push + new fixtures) を選択し、
GitHub 上の痕跡を完全消去 + test architecture 保持 + 新 PMC OA fixture
追加を 1 セッション (~6.5h) で完遂.

## 主要成果

| 指標 | Day22 末 | Day23 末 |
|:---|:---:|:---:|
| 全 tests | 101 passed / 1 skipped | <new count> passed / 1 skipped |
| Vancouver fixture | vancouver_24refs (OneDrive 由来) | vancouver_<N>refs (PMC OA <id>) |
| MDPI fixture | mdpi_149refs (出典不明) | mdpi_<N>refs (PMC OA <id>) |
| repo visibility | PUBLIC | PUBLIC (Day23 中に一時 Private 経由) |
| 機密性懸念 fixture | 2 件 (Public で露出) | 0 件 (history からも消去) |
| .git size | <old> | <new> (~1.5MB 削減) |

## Day23 archive 構成

- `README.md` — 本ファイル (Day23 index)
- `DAY23_LESSONS_LEARNED.md` — Day23 教訓記録
- `../../superpowers/specs/2026-05-24-day23-fixture-remediation-design.md` — Day23 spec
- `../../superpowers/plans/2026-05-24-day23-fixture-remediation.md` — Day23 plan

## Day23 commits

(filter-repo 後の新 SHA で記載)

| # | SHA | type | summary |
|:---:|:---|:---|:---|
| 1 | `<new>` | docs(spec) | Day23 fixture remediation spec |
| 2 | `<new>` | docs(plan) | Day23 implementation plan |
| 3 | `<new>` | chore(remove) | vancouver/mdpi fixture + tests 削除 |
| (filter-repo + force push, no commit) |||
| 4 | `<new>` | chore(security) | .gitleaksignore Day19 fingerprint refresh |
| 5 | `<new>` | docs(sessions) | Day22 archive SHA 表更新 |
| 6 | `<new>` | feat(fixtures) | Vancouver + MDPI replacement fixtures + build tools |
| 7 | `<new>` | test(integration) | 新 integration tests 8+8 |
| 8 | `<new>` | docs(sessions) | Day23 archive (本 commit) |

## Day24+ 候補

- pre-commit hook gitleaks 自動実行 (Day22 handoff パターン 3)
- CONTRIBUTING.md / Issue PR template (Day22 handoff パターン 2)
- PyPI 公開 (v0.2.0 候補)
- pyproject.toml + uv.lock 移行 (CLAUDE.md §8 整合)
- Crossref graceful failure 16 件の対応 (Day22 §6.3 NEW)
- NLM fuzzy-match precision 改善 (Day22 §6.3 NEW)
- tools/build_*_fixture.py の共通 utility への refactor (4 tools 出揃ったため)
```

- [ ] **Step 6: Create Day23 LESSONS_LEARNED.md**

Use `docs/sessions/day22/DAY22_LESSONS_LEARNED.md` as template. Key sections (§1-8):

  - §1 概要
  - §2 brainstorming 段階 (Q1-Q7 表)
  - §3 実装段階の経緯 (Phase 0-6 + 各 task の commit chain)
  - §4 設計判断と検証 (Pattern C の選定理由、filter-repo 検証、tag 再付与)
  - §5 実機検証 (filter-repo 前後 size、test count、release URL、gitleaks)
  - §6 教訓:
    - **D23-1**: 査読由来コンテンツの fixture 化はリスク、出典明示と PMC OA 縛りを default に
    - **D23-2**: filter-repo + force push は最終手段、Private 切替で exposure clock 停止が最初
    - **D23-3**: README が空の fixture は出典不明 → 公開前 audit で全 fixture に README 必須
  - §7 残存タスク (Day24+ 候補、Day22 §6.3 NEW を継承)
  - §8 次セッション再開プロンプトテンプレート (CONTRIBUTING.md / pre-commit / PyPI 等)

Target: 150-200 lines.

- [ ] **Step 7: gitleaks final check + commit Day23 archive**

```bash
gitleaks detect --no-banner --redact 2>&1 | tail -3
git add docs/sessions/day23/
git commit -m "$(cat <<'EOF'
docs(sessions): archive day23 fixture remediation session

Day23 セッション (2026-05-24) の archive.

構成:
  - Phase 0 (Pre-flight): backup + SHA snapshot + filter-repo install
  - Phase 1 (Soft delete): vancouver_24refs + mdpi_149refs fixture/test 削除
  - Phase 2 (Destructive): filter-repo で全 history から 2 path strip
  - Phase 3 (Destructive): force push + v0.1.0 tag/release 再作成
  - Phase 4 (Recovery): .gitleaksignore + Day22 archive SHA 表 + memory file
    の SHA refresh
  - Phase 5 (New fixtures): PMC 検索 → user 選定 → 新 fixture 構築 →
    integration test 追加 (apa/cell 8-test template 流用)
  - Phase 6: 再 Public + Day23 archive (本 commit)

成果:
  - 全 tests: 101 passed → <new> passed (vancouver + mdpi 削除 -9、新
    fixture +16 で純増), 1 skipped
  - 機密性懸念 fixture: 2 件 (Public 露出) → 0 件 (history からも消去)
  - 新 fixture: PMC OA CC BY 4.0 由来、出典 README で明示
  - tools: build_apa/build_cell に加え build_vancouver_replacement +
    build_mdpi_replacement を追加

教訓:
  - D23-1: 査読由来 fixture はリスク、PMC OA + 出典明示を default に
  - D23-2: filter-repo + force push は最終手段、Private 切替で exposure
    停止を最優先
  - D23-3: 公開前 audit で全 fixture の README 必須化 (mdpi_149refs に
    README が無かった事例から)

Day22 末の Day23+ 候補 (CONTRIBUTING.md, pre-commit hook, PyPI 等) は
Day24+ に継承.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

- [ ] **Step 8: Final verification**

```bash
git status
git log --oneline -10
python3 -m pytest tests/ -q 2>&1 | tail -3
gh repo view --json visibility,isPrivate
gh release view v0.1.0 --json tagName,isDraft
gh run list --limit 1 --json conclusion,status
curl -sI "https://github.com/hikataya01-netizen/pubmed-reference-resolver/releases/tag/v0.1.0" | head -1
```

Expected: working tree clean, ~108 tests passed, repo PUBLIC, release v0.1.0 not draft, CI success, release URL HTTP 200. **Checkpoint #6 passed.** Day23 complete.

---

## Self-Review Summary

| Check | Result |
|:---|:---|
| Spec coverage | §1-2 (background) → Task 0 (plan); §3 (Phase 2-3 destructive) → Task 3-4 with gates; §4 (new fixtures) → Task 8-10; §5 (cross-cutting) → Task 5-7; §6 (15 完了条件) → Task 11 Step 8 (final verification); §7 (commit plan) → 10 tasks with explicit commits; §8 (工数) → embedded in plan; §9 (risks) → embedded in each task's destructive operations |
| Placeholder scan | `<N>` (new fixture ref count) and `<X>` (new test distribution) and `<new>` (SHA) are runtime-substituted placeholders, intentional. `<id>`, `<Journal>` etc. depend on user PMC selection. All other content is concrete. |
| Type consistency | `EXPECTED_THREE_CLASS_DISTRIBUTION` literal name unchanged. `_SSL_CONTEXT` not touched (Day22 work). Path names `vancouver_<N>refs` / `mdpi_<N>refs` consistent across Task 8/9/10. |
| Destructive gate enforcement | Task 3 Step 1 (Gate #A) + Task 4 Step 1 (Gate #B) both stop and require explicit user "yes" before proceeding. |

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-24-day23-fixture-remediation.md`. Two execution options:

1. **Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks, fast iteration. Each destructive task (Task 3, Task 4) requires user approval before subagent dispatch.

2. **Inline Execution** — execute tasks in this session with checkpoints for human review.

Choose by responding with `subagent` or `inline`.
