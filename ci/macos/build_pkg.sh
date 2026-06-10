#!/usr/bin/env bash
set -euo pipefail

APP_NAME="${APP_NAME:-GorizontVS-VDI}"
APP_BUNDLE="${APP_BUNDLE:-GorizontVS-VDI.app}"
APP_VERSION="${APP_VERSION:-1.8}"
PKG_IDENTIFIER="${PKG_IDENTIFIER:-ru.gorizont.vdi}"
DEPLOY_TARGET="${MACOSX_DEPLOYMENT_TARGET:-14.0}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

BUILD_DIR="$ROOT_DIR/build"
APP_DIR="$ROOT_DIR/dist/$APP_BUNDLE"
APP_BIN="$APP_DIR/Contents/MacOS/$APP_NAME"

RESOURCES_DIR="$APP_DIR/Contents/Resources"
SPICE_DST="$RESOURCES_DIR/spice"
FRAMEWORKS_DST="$APP_DIR/Contents/Frameworks"

PKGROOT="$BUILD_DIR/pkgroot"
APP_INSTALL_DIR="$PKGROOT/Applications"

COMPONENT_PKG="$BUILD_DIR/component.pkg"

GIT_SHA_SHORT="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
RUN_ID="${GITHUB_RUN_NUMBER:-local}"

FINAL_PKG="$BUILD_DIR/GorizontVS-VDI-Client-Setup-${APP_VERSION}-${RUN_ID}-${GIT_SHA_SHORT}-macos14-arm64.pkg"

echo "==> Clean package build dir"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

echo "==> Use app bundle directly from dist"
test -d "$APP_DIR"
test -x "$APP_BIN"

echo "APP_DIR=$APP_DIR"
echo "APP_BIN=$APP_BIN"

if [ -e "$APP_DIR/Contents/MacOS/${APP_NAME}.real" ]; then
  echo "ERROR: ${APP_NAME}.real must not exist"
  ls -la "$APP_DIR/Contents/MacOS"
  exit 1
fi

echo "==> Prepare app internal directories"
mkdir -p "$SPICE_DST"
mkdir -p "$FRAMEWORKS_DST"

echo "==> Copy built SPICE files into dist app"

if [ ! -d "spice-full/build/spice/opt/homebrew" ]; then
  echo "ERROR: spice-full/build/spice/opt/homebrew not found"
  find spice-full/build/spice -maxdepth 5 -type d 2>/dev/null || true
  exit 1
fi

rsync -a --delete \
  "spice-full/build/spice/opt/homebrew/" \
  "$SPICE_DST/"

echo "==> Copy GStreamer runtime/plugins/codecs into dist app"

mkdir -p "$SPICE_DST/bin"
mkdir -p "$SPICE_DST/lib"
mkdir -p "$SPICE_DST/lib/gstreamer-1.0"
mkdir -p "$SPICE_DST/libexec/gstreamer-1.0"
mkdir -p "$SPICE_DST/share"

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

echo "==> Remove problematic/unneeded GStreamer plugins"

rm -f "$SPICE_DST/lib/gstreamer-1.0/libgstpython.dylib" || true
rm -f "$SPICE_DST/lib/gstreamer-1.0/libgstgtk4.dylib" || true
rm -f "$SPICE_DST/lib/gstreamer-1.0/libgstgtk.dylib" || true

if [ -d "/opt/homebrew/libexec/gstreamer-1.0" ]; then
  rsync -a "/opt/homebrew/libexec/gstreamer-1.0/" "$SPICE_DST/libexec/gstreamer-1.0/"
fi

if [ -d "/opt/homebrew/opt/gstreamer/libexec/gstreamer-1.0" ]; then
  rsync -a "/opt/homebrew/opt/gstreamer/libexec/gstreamer-1.0/" "$SPICE_DST/libexec/gstreamer-1.0/"
fi

for tool in gst-inspect-1.0 gst-launch-1.0 gst-discoverer-1.0; do
  if [ -x "/opt/homebrew/bin/$tool" ]; then
    cp -f "/opt/homebrew/bin/$tool" "$SPICE_DST/bin/$tool"
    chmod +x "$SPICE_DST/bin/$tool"
  fi
done

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

echo "==> Check gst-plugin-scanner"

if [ ! -x "$SPICE_DST/libexec/gstreamer-1.0/gst-plugin-scanner" ]; then
  echo "ERROR: gst-plugin-scanner not found"
  find "$SPICE_DST/libexec" -maxdepth 5 -type f || true
  exit 1
fi

echo "==> List copied GST plugins"

find "$SPICE_DST/lib/gstreamer-1.0" -maxdepth 1 -type f -name "*.dylib" | sort | sed 's#^#GST_PLUGIN: #'

echo "==> Bundle dylib dependencies for SPICE/Frameworks only"

ci/macos/bundle_dylibs.sh "$APP_DIR"

echo "==> Remove GTK4 libraries, keep GTK3 for spicy"

rm -f "$FRAMEWORKS_DST"/libgtk-4*.dylib || true
rm -f "$FRAMEWORKS_DST"/libgdk-4*.dylib || true
rm -f "$FRAMEWORKS_DST"/libgraphene-1.0*.dylib || true

echo "==> Check SPICE spicy rpaths"

SPICY_BIN="$SPICE_DST/bin/spicy"

if [ -x "$SPICY_BIN" ]; then
  echo "spicy exists: $SPICY_BIN"
  otool -l "$SPICY_BIN" | grep -A2 LC_RPATH || true
  otool -L "$SPICY_BIN" || true

  if ! otool -l "$SPICY_BIN" | grep -q "@loader_path/../lib"; then
    echo "ERROR: spicy has no @loader_path/../lib rpath"
    exit 1
  fi

  if ! otool -l "$SPICY_BIN" | grep -q "@loader_path/../../../Frameworks"; then
    echo "ERROR: spicy has no @loader_path/../../../Frameworks rpath"
    exit 1
  fi
else
  echo "ERROR: spicy binary not found or not executable: $SPICY_BIN"
  find "$SPICE_DST" -maxdepth 5 -type f -name "spicy" -print || true
  exit 1
fi

echo "==> Keep Nuitka/PySide runtime untouched"

echo "==> Patch Info.plist"

PLIST="$APP_DIR/Contents/Info.plist"

/usr/libexec/PlistBuddy -c "Set :LSMinimumSystemVersion $DEPLOY_TARGET" "$PLIST" 2>/dev/null || \
/usr/libexec/PlistBuddy -c "Add :LSMinimumSystemVersion string $DEPLOY_TARGET" "$PLIST"

/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $APP_VERSION" "$PLIST" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Set :CFBundleVersion $APP_VERSION" "$PLIST" 2>/dev/null || true

echo "==> Permissions"

chmod -R u+w "$APP_DIR" || true
chmod -R a+rX "$APP_DIR"
chmod +x "$APP_BIN"

if [ -d "$SPICE_DST/bin" ]; then
  find "$SPICE_DST/bin" -type f -exec chmod +x {} + 2>/dev/null || true
fi

if [ -f "$SPICE_DST/libexec/gstreamer-1.0/gst-plugin-scanner" ]; then
  chmod +x "$SPICE_DST/libexec/gstreamer-1.0/gst-plugin-scanner" || true
fi

echo "==> Remove broken symlinks in SPICE/Frameworks only"

if [ -d "$SPICE_DST" ]; then
  find "$SPICE_DST" -xtype l -print -delete 2>/dev/null || true
fi

if [ -d "$FRAMEWORKS_DST" ]; then
  find "$FRAMEWORKS_DST" -xtype l -print -delete 2>/dev/null || true
fi

echo "==> Clear xattrs in SPICE/Frameworks only"

if [ -d "$SPICE_DST" ]; then
  find "$SPICE_DST" -type f -exec xattr -c {} + 2>/dev/null || true
  find "$SPICE_DST" -type d -exec xattr -c {} + 2>/dev/null || true
fi

if [ -d "$FRAMEWORKS_DST" ]; then
  find "$FRAMEWORKS_DST" -type f -exec xattr -c {} + 2>/dev/null || true
  find "$FRAMEWORKS_DST" -type d -exec xattr -c {} + 2>/dev/null || true
fi

echo "==> Ad-hoc sign Mach-O files in SPICE/Frameworks only"

for root in "$SPICE_DST" "$FRAMEWORKS_DST"; do
  if [ ! -d "$root" ]; then
    continue
  fi

  find "$root" -type f -print0 | while IFS= read -r -d '' file_path; do
    if file "$file_path" 2>/dev/null | grep -q "Mach-O"; then
      echo "SIGN: $file_path"
      chmod u+w "$file_path" || true
      codesign --remove-signature "$file_path" 2>/dev/null || true
      codesign --force --sign - --timestamp=none "$file_path" || true
    fi
  done
done

echo "==> Do not codesign app bundle itself"
echo "==> Do not touch Contents/MacOS Nuitka/PySide runtime"

echo "==> Check removed problematic GST plugins"

for bad_plugin in \
  "$SPICE_DST/lib/gstreamer-1.0/libgstpython.dylib" \
  "$SPICE_DST/lib/gstreamer-1.0/libgstgtk4.dylib" \
  "$SPICE_DST/lib/gstreamer-1.0/libgstgtk.dylib"
do
  if [ -e "$bad_plugin" ]; then
    echo "ERROR: bad GStreamer plugin still exists: $bad_plugin"
    exit 1
  fi
done

echo "==> Check no /opt/homebrew refs in SPICE/Frameworks only"

bad_homebrew=0

while IFS= read -r macho; do
  if file "$macho" | grep -q "Mach-O"; then
    if otool -L "$macho" 2>/dev/null | grep -q "/opt/homebrew"; then
      echo "BAD HOMEBREW REF: $macho"
      otool -L "$macho" 2>/dev/null | grep "/opt/homebrew" || true
      bad_homebrew=1
    fi
  fi
done < <(
  {
    find "$SPICE_DST" -type f -print
    find "$FRAMEWORKS_DST" -type f -print
  } | sort -u
)

if [ "$bad_homebrew" -eq 1 ]; then
  echo "ERROR: unresolved /opt/homebrew references remained in SPICE/Frameworks"
  exit 1
fi

echo "==> Final app structure before pkgroot copy"

ls -la "$APP_DIR/Contents/MacOS"
test -x "$APP_BIN"

if [ -e "$APP_DIR/Contents/MacOS/${APP_NAME}.real" ]; then
  echo "ERROR: ${APP_NAME}.real must not exist"
  exit 1
fi

find "$APP_DIR" -maxdepth 4 -type f | sort | head -300

echo "==> Build component.pkg from explicit pkgroot"

rm -rf "$PKGROOT"
mkdir -p "$APP_INSTALL_DIR"

rsync -a --delete \
  "$APP_DIR/" \
  "$APP_INSTALL_DIR/$APP_BUNDLE/"

test -d "$APP_INSTALL_DIR/$APP_BUNDLE"
test -x "$APP_INSTALL_DIR/$APP_BUNDLE/Contents/MacOS/$APP_NAME"

echo "==> Payload app path:"
ls -la "$APP_INSTALL_DIR"
ls -la "$APP_INSTALL_DIR/$APP_BUNDLE/Contents/MacOS"

echo "==> Payload files preview:"
find "$PKGROOT" -maxdepth 4 -type f | sort | head -200

pkgbuild \
  --root "$PKGROOT" \
  --scripts "$ROOT_DIR/ci/macos" \
  --identifier "$PKG_IDENTIFIER" \
  --version "$APP_VERSION" \
  --install-location "/" \
  "$COMPONENT_PKG"

echo "==> Create product requirements"

cat > "$BUILD_DIR/product-requirements.plist" <<EOF
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

productbuild \
  --product "$BUILD_DIR/product-requirements.plist" \
  --package "$COMPONENT_PKG" \
  "$FINAL_PKG"

echo "==> Done"

ls -lh "$FINAL_PKG"

echo "==> Final PKG payload preview"
pkgutil --payload-files "$FINAL_PKG" | head -50
