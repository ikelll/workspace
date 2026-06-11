#!/usr/bin/env bash
set -euo pipefail

APP_NAME="${APP_NAME:-GorizontVS-VDI}"
APP_BUNDLE="${APP_BUNDLE:-GorizontVS-VDI.app}"
APP_VERSION="${APP_VERSION:-1.8}"
PKG_IDENTIFIER="${PKG_IDENTIFIER:-ru.gorizont.vdi}"
DEPLOY_TARGET="${MACOSX_DEPLOYMENT_TARGET:-14.0}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

PAYLOAD_DIR="$ROOT_DIR/build/pkgroot"
APP_DST="$PAYLOAD_DIR/Applications/$APP_BUNDLE"

echo "==> Clean old build"
rm -rf "$ROOT_DIR/build"

echo "==> Create clean payload"
mkdir -p "$PAYLOAD_DIR/Applications"

echo "==> Copy Nuitka/PySide app as-is"
cp -a "dist/$APP_BUNDLE" "$PAYLOAD_DIR/Applications/"

test -d "$APP_DST"
test -x "$APP_DST/Contents/MacOS/$APP_NAME"

echo "==> Patch Info.plist minimum macOS"

PLIST="$APP_DST/Contents/Info.plist"

/usr/libexec/PlistBuddy -c "Set :LSMinimumSystemVersion $DEPLOY_TARGET" "$PLIST" 2>/dev/null || \
/usr/libexec/PlistBuddy -c "Add :LSMinimumSystemVersion string $DEPLOY_TARGET" "$PLIST"

/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $APP_VERSION" "$PLIST" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Set :CFBundleVersion $APP_VERSION" "$PLIST" 2>/dev/null || true

echo "==> Permissions"

chmod -R u+w "$APP_DST" || true
chmod -R a+rX "$APP_DST"
chmod +x "$APP_DST/Contents/MacOS/$APP_NAME"

echo "==> Remove old signatures and xattrs"

find "$APP_DST" -name "_CodeSignature" -type d -prune -exec rm -rf {} \; 2>/dev/null || true
find "$APP_DST" -xtype l -print -delete 2>/dev/null || true

find "$APP_DST" -type f -exec xattr -c {} + 2>/dev/null || true
find "$APP_DST" -type d -exec xattr -c {} + 2>/dev/null || true

echo "==> Ad-hoc sign all Mach-O files"

find "$APP_DST" -type f -print0 | while IFS= read -r -d '' file_path; do
  if file "$file_path" 2>/dev/null | grep -q "Mach-O"; then
    echo "SIGN: $file_path"
    chmod u+w "$file_path" || true
    codesign --remove-signature "$file_path" 2>/dev/null || true
    codesign --force --sign - --timestamp=none "$file_path"
  fi
done

echo "==> Ad-hoc sign app bundle"

codesign --remove-signature "$APP_DST" 2>/dev/null || true
codesign --force --sign - --timestamp=none "$APP_DST"

echo "==> Verify app bundle signature"

codesign --verify --verbose=4 "$APP_DST"

echo "==> Verify every Mach-O signature"

bad_sign=0

while IFS= read -r f; do
  if file "$f" 2>/dev/null | grep -q "Mach-O"; then
    if ! codesign --verify --verbose=1 "$f" >/dev/null 2>&1; then
      echo "BAD SIGN: $f"
      bad_sign=1
    fi
  fi
done < <(find "$APP_DST" -type f -print)

if [ "$bad_sign" -eq 1 ]; then
  echo "ERROR: some Mach-O files are not signed correctly"
  exit 1
fi

echo "==> Check no /opt/homebrew refs"

bad_homebrew=0

while IFS= read -r f; do
  if file "$f" 2>/dev/null | grep -q "Mach-O"; then
    if otool -L "$f" 2>/dev/null | grep -q "/opt/homebrew"; then
      echo "BAD HOMEBREW REF: $f"
      otool -L "$f" 2>/dev/null | grep "/opt/homebrew" || true
      bad_homebrew=1
    fi
  fi
done < <(find "$APP_DST" -type f -print)

if [ "$bad_homebrew" -eq 1 ]; then
  echo "ERROR: unresolved /opt/homebrew references remained"
  exit 1
fi

echo "==> Show app structure"

find "$APP_DST" -maxdepth 4 -type f | sort | head -300

echo "==> Analyze component"

pkgbuild --analyze \
  --root "$PAYLOAD_DIR" \
  "$ROOT_DIR/build/component.plist"

/usr/libexec/PlistBuddy -c "Set :0:BundleIsRelocatable false" "$ROOT_DIR/build/component.plist" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Set :0:BundleOverwriteAction upgrade" "$ROOT_DIR/build/component.plist" 2>/dev/null || true

echo "==> Build component.pkg"

pkgbuild \
  --root "$PAYLOAD_DIR" \
  --component-plist "$ROOT_DIR/build/component.plist" \
  --scripts "$ROOT_DIR/ci/macos/client-only-scripts" \
  --identifier "$PKG_IDENTIFIER" \
  --version "$APP_VERSION" \
  --install-location "/" \
  "$ROOT_DIR/build/component.pkg"

echo "==> Create product requirements"

cat > "$ROOT_DIR/build/product-requirements.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>os</key>
    <array>
      <string>${DEPLOY_TARGET}</string>
    </array>
  </dict>
</plist>
EOF

echo "==> Build final unsigned PKG"

FINAL_PKG="$ROOT_DIR/build/GorizontVS-VDI-Client-Only-${APP_VERSION}-macos14-arm64.pkg"

productbuild \
  --product "$ROOT_DIR/build/product-requirements.plist" \
  --package "$ROOT_DIR/build/component.pkg" \
  "$FINAL_PKG"

echo "==> Done"

ls -lh "$FINAL_PKG"
