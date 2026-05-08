#!/bin/sh

set -eu

REPO_ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
TARGET_DIR="${HOME}/.local/bin"
TARGET_PATH="${TARGET_DIR}/AutoCI"

mkdir -p "$TARGET_DIR"
chmod +x "$REPO_ROOT/AutoCI" "$REPO_ROOT/scripts/AutoCI"
ln -sf "$REPO_ROOT/AutoCI" "$TARGET_PATH"

echo "✅ AutoCI 설치 완료: $TARGET_PATH"
echo "이제 새 터미널에서 'AutoCI \"요구사항\"' 로 실행할 수 있습니다."
