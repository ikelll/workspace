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
APP_MACOS_DIR="$APP_DST/Contents/MacOS"
APP_RESOURCES_DIR="$APP_DST/Contents/Resources"
APP_FRAMEWORKS_DIR="$APP_DST/Contents/Frameworks"
SPICE_DST="$APP_RESOURCES_DIR/spice"

echo "==> Clean old build"
rm -rf "$ROOT_DIR/build"

echo "==> Create clean payload"
mkdir -p "$PAYLOAD_DIR/Applications"

echo "==> Copy client app from dist"
cp -a "dist/$APP_BUNDLE" "$PAYLOAD_DIR/Applications/"

test -d "$APP_DST"
test -x "$APP_MACOS_DIR/$APP_NAME"

echo "==> Prepare directories"
mkdir -p "$APP_FRAMEWORKS_DIR"
mkdir -p "$SPICE_DST/bin"
mkdir -p "$SPICE_DST/lib"
mkdir -p "$SPICE_DST/lib/gstreamer-1.0"
mkdir -p "$SPICE_DST/libexec/gstreamer-1.0"
mkdir -p "$SPICE_DST/share"

echo "==> Copy built SPICE prefix"

if [ ! -d "spice-full/build/spice/opt/homebrew" ]; then
  echo "ERROR: spice-full/build/spice/opt/homebrew not found"
  find spice-full/build/spice -maxdepth 6 -type d 2>/dev/null || true
  exit 1
fi

rsync -a "spice-full/build/spice/opt/homebrew/" "$SPICE_DST/"

test -x "$SPICE_DST/bin/spicy"

echo "==> Copy GStreamer plugins/runtime"

if [ -d "/opt/homebrew/lib/gstreamer-1.0" ]; then
  rsync -a "/opt/homebrew/lib/gstreamer-1.0/" "$SPICE_DST/lib/gstreamer-1.0/"
fi

for gst_plugin_dir in \
  "/opt/homebrew/opt/gstreamer/lib/gstreamer-1.0" \
  "/opt/homebrew/opt/gst-plugins-base/lib/gstreamer-1.0" \
  "/opt/homebrew/opt/gst-plugins-good/lib/gstreamer-1.0" \
  "/opt/homebrew/opt/gst-plugins-bad/lib/gstreamer-1.0" \
  "/opt/homebrew/opt/gst-libav/lib/gstreamer-1.0"
do
  if [ -d "$gst_plugin_dir" ]; then
    echo "Copy GST plugins: $gst_plugin_dir"
    rsync -a "$gst_plugin_dir/" "$SPICE_DST/lib/gstreamer-1.0/"
  fi
done

echo "==> Remove problematic GStreamer plugins"

rm -f "$SPICE_DST/lib/gstreamer-1.0/libgstpython.dylib" || true
rm -f "$SPICE_DST/lib/gstreamer-1.0/libgstgtk4.dylib" || true
rm -f "$SPICE_DST/lib/gstreamer-1.0/libgstgtk.dylib" || true

echo "==> Copy gst-plugin-scanner"

if [ -d "/opt/homebrew/libexec/gstreamer-1.0" ]; then
  rsync -a "/opt/homebrew/libexec/gstreamer-1.0/" "$SPICE_DST/libexec/gstreamer-1.0/"
fi

if [ -d "/opt/homebrew/opt/gstreamer/libexec/gstreamer-1.0" ]; then
  rsync -a "/opt/homebrew/opt/gstreamer/libexec/gstreamer-1.0/" "$SPICE_DST/libexec/gstreamer-1.0/"
fi

test -x "$SPICE_DST/libexec/gstreamer-1.0/gst-plugin-scanner"

echo "==> Copy optional GStreamer tools"

for tool in gst-inspect-1.0 gst-launch-1.0 gst-discoverer-1.0; do
  if [ -x "/opt/homebrew/bin/$tool" ]; then
    cp -f "/opt/homebrew/bin/$tool" "$SPICE_DST/bin/$tool"
    chmod +x "$SPICE_DST/bin/$tool"
  fi
done

echo "==> Copy GLib/GStreamer data"

for src in \
  "/opt/homebrew/share/gstreamer-1.0" \
  "/opt/homebrew/share/glib-2.0" \
  "/opt/homebrew/share/locale"
do
  if [ -d "$src" ]; then
    dst="$SPICE_DST/share/$(basename "$src")"
    mkdir -p "$dst"
    rsync -a "$src/" "$dst/"
  fi
done

echo "==> Bundle dylibs and fix rpaths"
ci/macos/bundle_dylibs_spicy.sh "$APP_DST"

echo "==> Remove duplicate/unwanted Frameworks libs"

rm -f "$APP_FRAMEWORKS_DIR"/Qt* || true
rm -f "$APP_FRAMEWORKS_DIR"/libQt* || true
rm -f "$APP_FRAMEWORKS_DIR"/Python || true
rm -f "$APP_FRAMEWORKS_DIR"/libpython* || true
rm -f "$APP_FRAMEWORKS_DIR"/libgtk-4*.dylib || true
rm -f "$APP_FRAMEWORKS_DIR"/libgdk-4*.dylib || true

echo "==> Create compatibility spicy wrapper in Contents/MacOS"

cat > "$APP_MACOS_DIR/spicy" <<'EOF'
#!/bin/bash
set -e

APP_MACOS_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_CONTENTS_DIR="$(cd "$APP_MACOS_DIR/.." && pwd)"
APP_RESOURCES_DIR="$APP_CONTENTS_DIR/Resources"
APP_FRAMEWORKS_DIR="$APP_CONTENTS_DIR/Frameworks"
SPICE_DIR="$APP_RESOURCES_DIR/spice"

mkdir -p "$HOME/Library/Application Support/GorizontVS" || true

export PATH="$SPICE_DIR/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

export DYLD_FALLBACK_LIBRARY_PATH="$APP_FRAMEWORKS_DIR:$SPICE_DIR/lib:$SPICE_DIR/lib/gstreamer-1.0:/usr/lib"

export GST_PLUGIN_PATH_1_0="$SPICE_DIR/lib/gstreamer-1.0"
export GST_PLUGIN_SCANNER="$SPICE_DIR/libexec/gstreamer-1.0/gst-plugin-scanner"
export GST_REGISTRY_REUSE_PLUGIN_SCANNER=1
export GST_REGISTRY="$HOME/Library/Application Support/GorizontVS/gstreamer-registry.bin"

export GIO_MODULE_DIR="$SPICE_DIR/lib/gio/modules"
export GI_TYPELIB_PATH="$SPICE_DIR/lib/girepository-1.0"

exec "$SPICE_DIR/bin/spicy" "$@"
EOF

chmod +x "$APP_MACOS_DIR/spicy"

echo "==> Patch Info.plist"

PLIST="$APP_DST/Contents/Info.plist"

/usr/libexec/PlistBuddy -c "Set :LSMinimumSystemVersion $DEPLOY_TARGET" "$PLIST" 2>/dev/null || \
/usr/libexec/PlistBuddy -c "Add :LSMinimumSystemVersion string $DEPLOY_TARGET" "$PLIST"

/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $APP_VERSION" "$PLIST" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Set :CFBundleVersion $APP_VERSION" "$PLIST" 2>/dev/null || true

echo "==> Validate structure"

test -x "$APP_MACOS_DIR/$APP_NAME"
test -x "$APP_MACOS_DIR/spicy"
test -x "$SPICE_DST/bin/spicy"
test -x "$SPICE_DST/libexec/gstreamer-1.0/gst-plugin-scanner"

echo "==> Permissions"

chmod -R u+w "$APP_DST" || true
chmod -R a+rX "$APP_DST"

chmod +x "$APP_MACOS_DIR/$APP_NAME"
chmod +x "$APP_MACOS_DIR/spicy"
chmod +x "$SPICE_DST/bin/spicy"
chmod +x "$SPICE_DST/libexec/gstreamer-1.0/gst-plugin-scanner"

find "$SPICE_DST/bin" -type f -exec chmod +x {} + 2>/dev/null || true
find "$SPICE_DST/libexec" -type f -exec chmod +x {} + 2>/dev/null || true

echo "==> Remove stale signatures, xattrs, broken symlinks"

find "$APP_DST" -name "_CodeSignature" -type d -prune -exec rm -rf {} \; 2>/dev/null || true
find "$APP_DST" -xtype l -print -delete 2>/dev/null || true

find "$APP_DST" -type f -exec xattr -c {} + 2>/dev/null || true
find "$APP_DST" -type d -exec xattr -c {} + 2>/dev/null || true

echo "==> Sign every Mach-O"

find "$APP_DST" -type f -print0 | while IFS= read -r -d '' f; do
  if file "$f" 2>/dev/null | grep -q "Mach-O"; then
    echo "SIGN: $f"
    chmod u+w "$f" || true
    codesign --remove-signature "$f" 2>/dev/null || true
    codesign --force --sign - --timestamp=none "$f"
  fi
done

echo "==> Sign app bundle"

codesign --remove-signature "$APP_DST" 2>/dev/null || true
codesign --force --sign - --timestamp=none "$APP_DST"

echo "==> Verify app bundle"

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

echo "==> Verify no /opt/homebrew references"

bad_homebrew=0

while IFS= read -r f; do
  if file "$f" 2>/dev/null | grep -q "Mach-O"; then
    if otool -L "$f" 2>/dev/null | grep -q "/opt/homebrew"; then
      echo "BAD HOMEBREW REF: $f"
      otool -L "$f" | grep "/opt/homebrew" || true
      bad_homebrew=1
    fi
  fi
done < <(find "$APP_DST" -type f -print)

if [ "$bad_homebrew" -eq 1 ]; then
  echo "ERROR: unresolved /opt/homebrew references remained"
  exit 1
fi

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
  --scripts "$ROOT_DIR/ci/macos/spicy-scripts" \
  --identifier "$PKG_IDENTIFIER" \
  --version "$APP_VERSION" \
  --install-location "/" \
  "$ROOT_DIR/build/component.pkg"

echo "==> Build final PKG"

FINAL_PKG="$ROOT_DIR/build/GorizontVS-VDI-With-SPICE-${APP_VERSION}-macos14-arm64.pkg"

productbuild \
  --package "$ROOT_DIR/build/component.pkg" \
  "$FINAL_PKG"

echo "==> Done"

ls -lh "$FINAL_PKG"
