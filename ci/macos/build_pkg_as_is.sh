#!/usr/bin/env bash
set -euo pipefail

APP_BUNDLE="${APP_BUNDLE:-GorizontVS-VDI.app}"
APP_VERSION="${APP_VERSION:-1.8}"
PKG_IDENTIFIER="${PKG_IDENTIFIER:-ru.gorizont.vdi}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

PAYLOAD_DIR="$ROOT_DIR/build/pkgroot"
APP_DST="$PAYLOAD_DIR/Applications/$APP_BUNDLE"

echo "==> Clean old build"
rm -rf "$ROOT_DIR/build"

echo "==> Create payload"
mkdir -p "$PAYLOAD_DIR/Applications"

echo "==> Copy dist app as-is"
cp -a "dist/$APP_BUNDLE" "$PAYLOAD_DIR/Applications/"

echo "==> Check copied app"
test -d "$APP_DST"
test -x "$APP_DST/Contents/MacOS/GorizontVS-VDI"

echo "==> Show app structure"
find "$APP_DST" -maxdepth 4 -type f | sort | head -300

echo "==> Build component.pkg"

pkgbuild \
  --root "$PAYLOAD_DIR" \
  --identifier "$PKG_IDENTIFIER" \
  --version "$APP_VERSION" \
  --install-location "/" \
  "$ROOT_DIR/build/component.pkg"

echo "==> Build final PKG"

FINAL_PKG="$ROOT_DIR/build/GorizontVS-VDI-As-Is-${APP_VERSION}-macos14-arm64.pkg"

productbuild \
  --package "$ROOT_DIR/build/component.pkg" \
  "$FINAL_PKG"

echo "==> Done"
ls -lh "$FINAL_PKG"
