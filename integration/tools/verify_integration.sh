#!/bin/bash
# verify_integration.sh — パッチ 01 + 02 の適用 → 動作確認を自動化
# 使い方: ./integration/tools/verify_integration.sh
set -e

echo "[1/4] Patch 01 --check"
git apply --check integration/patches/01_split_references_fix.patch

echo "[2/4] Patch 01 適用"
git apply integration/patches/01_split_references_fix.patch

echo "[3/4] Patch 02 --check (Patch 01 適用済み状態で)"
git apply --check integration/patches/02_mdpi_fast_path.patch

echo "[4/4] Patch 02 適用"
git apply integration/patches/02_mdpi_fast_path.patch

echo ""
echo "✓ 両パッチとも適用成功"
echo ""
echo "次のステップ:"
echo "  1. python3 -c 'import main, mdpi_parser; print(\"imports OK\")'"
echo "  2. git add main.py mdpi_parser.py"
echo "  3. git commit (適切なメッセージで)"
