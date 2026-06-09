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
RESOURCES_DIR="$APP_DST/Contents/Resources"
SPICE_DST="$RESOURCES_DIR/spice"
FRAMEWORKS_DST="$APP_DST/Contents/Frameworks"

echo "==> Clean old build"
rm -rf "$ROOT_DIR/build"

echo "==> Create clean payload"
mkdir -p "$PAYLOAD_DIR/Applications"
mkdir -p "$SPICE_DST"
mkdir -p "$FRAMEWORKS_DST"

echo "==> Copy app bundle"
cp -a "dist/$APP_BUNDLE" "$PAYLOAD_DIR/Applications/"

test -d "$APP_DST"
test -x "$APP_DST/Contents/MacOS/$APP_NAME"

echo "==> Copy built SPICE files"

if [ ! -d "spice-full/build/spice/opt/homebrew" ]; then
  echo "ERROR: spice-full/build/spice/opt/homebrew not found"
  find spice-full/build/spice -maxdepth 5 -type d 2>/dev/null || true
  exit 1
fi

rsync -a "spice-full/build/spice/opt/homebrew/" "$SPICE_DST/"

echo "==> Copy GStreamer runtime/plugins/codecs from runner"

mkdir -p "$SPICE_DST/bin"
mkdir -p "$SPICE_DST/lib"
mkdir -p "$SPICE_DST/lib/gstreamer-1.0"
mkdir -p "$SPICE_DST/libexec/gstreamer-1.0"
mkdir -p "$SPICE_DST/share"

# Main GStreamer plugins directory.
if [ -d "/opt/homebrew/lib/gstreamer-1.0" ]; then
  rsync -a "/opt/homebrew/lib/gstreamer-1.0/" "$SPICE_DST/lib/gstreamer-1.0/"
fi

# Plugin directories from Homebrew formulas.
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

# Not needed for SPICE playback. It depends on Python runtime and causes:
# Library not loaded: @rpath/Python
rm -f "$SPICE_DST/lib/gstreamer-1.0/libgstpython.dylib" || true

# Do not load GTK4 into spicy GTK3 process.
# It causes duplicate Objective-C classes with GTK3:
# libgtk-3.0.dylib and libgtk-4.1.dylib
rm -f "$SPICE_DST/lib/gstreamer-1.0/libgstgtk4.dylib" || true

# Optional GTK sink plugin. Usually not needed for SPICE client playback.
rm -f "$SPICE_DST/lib/gstreamer-1.0/libgstgtk.dylib" || true

# gst-plugin-scanner.
if [ -d "/opt/homebrew/libexec/gstreamer-1.0" ]; then
  rsync -a "/opt/homebrew/libexec/gstreamer-1.0/" "$SPICE_DST/libexec/gstreamer-1.0/"
fi

if [ -d "/opt/homebrew/opt/gstreamer/libexec/gstreamer-1.0" ]; then
  rsync -a "/opt/homebrew/opt/gstreamer/libexec/gstreamer-1.0/" "$SPICE_DST/libexec/gstreamer-1.0/"
fi

# Optional GStreamer tools, useful for diagnostics.
for tool in gst-inspect-1.0 gst-launch-1.0 gst-discoverer-1.0; do
  if [ -x "/opt/homebrew/bin/$tool" ]; then
    cp -f "/opt/homebrew/bin/$tool" "$SPICE_DST/bin/$tool"
    chmod +x "$SPICE_DST/bin/$tool"
  fi
done

# GStreamer / GLib data.
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

echo "==> List copied GST plugins"
find "$SPICE_DST/lib/gstreamer-1.0" -maxdepth 1 -type f -name "*.dylib" | sort | sed 's#^#GST_PLUGIN: #'

echo "==> Check important GStreamer plugins"

required_gst_plugins=(
  "libgstcoreelements.dylib"
  "libgstplayback.dylib"
  "libgstvideoconvertscale.dylib"
  "libgstaudioconvert.dylib"
  "libgstaudioresample.dylib"
  "libgstapp.dylib"
  "libgstlibav.dylib"
  "libgstisomp4.dylib"
  "libgstmatroska.dylib"
  "libgstrtp.dylib"
  "libgstrtpmanager.dylib"
  "libgstrtsp.dylib"
  "libgstvideoparsersbad.dylib"
)

for plugin in "${required_gst_plugins[@]}"; do
  if [ -f "$SPICE_DST/lib/gstreamer-1.0/$plugin" ]; then
    echo "OK GST: $plugin"
  else
    echo "WARN GST MISSING: $plugin"
  fi
done

if [ ! -x "$SPICE_DST/libexec/gstreamer-1.0/gst-plugin-scanner" ]; then
  echo "ERROR: gst-plugin-scanner not found"
  find "$SPICE_DST/libexec" -maxdepth 5 -type f || true
  exit 1
fi

echo "==> Bundle dylib dependencies from runner"
ci/macos/bundle_dylibs.sh "$APP_DST"

echo "==> Remove GTK4 libraries, keep GTK3 for spicy"

# spicy is GTK3. GTK4 in the same process causes duplicate Objective-C classes.
rm -f "$APP_DST/Contents/Frameworks"/libgtk-4*.dylib || true
rm -f "$APP_DST/Contents/Frameworks"/libgdk-4*.dylib || true
rm -f "$APP_DST/Contents/Frameworks"/libgraphene-1.0*.dylib || true

echo "==> Check SPICE spicy rpaths"

SPICY_BIN="$APP_DST/Contents/Resources/spice/bin/spicy"

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

echo "==> Remove duplicated Qt/Python libraries from Frameworks"

rm -f "$APP_DST/Contents/Frameworks"/Qt* || true
rm -f "$APP_DST/Contents/Frameworks"/libQt* || true
rm -f "$APP_DST/Contents/Frameworks"/Python || true
rm -f "$APP_DST/Contents/Frameworks"/libpython* || true

echo "==> Check for duplicated Qt/Python libraries"

if find "$APP_DST/Contents/Frameworks" -maxdepth 1 -type f \( -name "Qt*" -o -name "libQt*" -o -name "Python" -o -name "libpython*" \) | grep -q .; then
  echo "ERROR: duplicated Qt/Python libraries found in Contents/Frameworks"
  find "$APP_DST/Contents/Frameworks" -maxdepth 1 -type f \( -name "Qt*" -o -name "libQt*" -o -name "Python" -o -name "libpython*" \)
  exit 1
fi

echo "==> Check no GTK4 libraries in Frameworks"

if find "$APP_DST/Contents/Frameworks" -maxdepth 1 -type f \( -name "libgtk-4*.dylib" -o -name "libgdk-4*.dylib" \) | grep -q .; then
  echo "ERROR: GTK4 libraries found in Contents/Frameworks"
  find "$APP_DST/Contents/Frameworks" -maxdepth 1 -type f \( -name "libgtk-4*.dylib" -o -name "libgdk-4*.dylib" \)
  exit 1
fi

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

echo "==> Create launcher wrapper"

BIN="$APP_DST/Contents/MacOS/$APP_NAME"
REAL_BIN="$APP_DST/Contents/MacOS/${APP_NAME}.real"

if [ ! -f "$REAL_BIN" ]; then
  mv "$BIN" "$REAL_BIN"

  cat > "$BIN" <<'EOF'
#!/bin/bash
set -e

APP_MACOS_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_CONTENTS_DIR="$(cd "$APP_MACOS_DIR/.." && pwd)"
APP_RESOURCES_DIR="$APP_CONTENTS_DIR/Resources"
APP_FRAMEWORKS_DIR="$APP_CONTENTS_DIR/Frameworks"
SPICE_DIR="$APP_RESOURCES_DIR/spice"

mkdir -p "$HOME/Library/Application Support/GorizontVS" || true

export PATH="$SPICE_DIR/bin:/usr/bin:/bin:/usr/sbin:/sbin"

export DYLD_FALLBACK_LIBRARY_PATH="$APP_FRAMEWORKS_DIR:$SPICE_DIR/lib:$SPICE_DIR/lib/gstreamer-1.0:/usr/lib"

export GST_PLUGIN_PATH_1_0="$SPICE_DIR/lib/gstreamer-1.0"
export GST_PLUGIN_SCANNER="$SPICE_DIR/libexec/gstreamer-1.0/gst-plugin-scanner"
export GST_REGISTRY_REUSE_PLUGIN_SCANNER=1
export GST_REGISTRY="$HOME/Library/Application Support/GorizontVS/gstreamer-registry.bin"

export GIO_MODULE_DIR="$SPICE_DIR/lib/gio/modules"
export GI_TYPELIB_PATH="$SPICE_DIR/lib/girepository-1.0"

exec "$APP_MACOS_DIR/GorizontVS-VDI.real" "$@"
EOF

  chmod +x "$BIN"
fi

echo "==> Patch Info.plist"

PLIST="$APP_DST/Contents/Info.plist"

/usr/libexec/PlistBuddy -c "Set :LSMinimumSystemVersion $DEPLOY_TARGET" "$PLIST" 2>/dev/null || \
/usr/libexec/PlistBuddy -c "Add :LSMinimumSystemVersion string $DEPLOY_TARGET" "$PLIST"

/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $APP_VERSION" "$PLIST" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Set :CFBundleVersion $APP_VERSION" "$PLIST" 2>/dev/null || true

echo "==> Check main executable"

ls -la "$APP_DST"
ls -la "$APP_DST/Contents"
ls -la "$APP_DST/Contents/MacOS"

test -d "$APP_DST"
test -f "$APP_DST/Contents/Info.plist"
test -x "$APP_DST/Contents/MacOS/$APP_NAME"
test -x "$APP_DST/Contents/MacOS/${APP_NAME}.real"

echo "==> Permissions"

chmod -R u+w "$APP_DST" || true
chmod -R a+rX "$APP_DST"
chmod +x "$APP_DST/Contents/MacOS/$APP_NAME"
chmod +x "$APP_DST/Contents/MacOS/${APP_NAME}.real"

if [ -d "$APP_DST/Contents/Resources/spice/bin" ]; then
  find "$APP_DST/Contents/Resources/spice/bin" -type f -exec chmod +x {} + 2>/dev/null || true
fi

if [ -f "$APP_DST/Contents/Resources/spice/libexec/gstreamer-1.0/gst-plugin-scanner" ]; then
  chmod +x "$APP_DST/Contents/Resources/spice/libexec/gstreamer-1.0/gst-plugin-scanner" || true
fi

echo "==> Remove broken symlinks before codesign"

find "$APP_DST" -xtype l -print -delete 2>/dev/null || true

echo "==> Clear xattrs"

find "$APP_DST" -type f -exec xattr -c {} + 2>/dev/null || true
find "$APP_DST" -type d -exec xattr -c {} + 2>/dev/null || true

echo "==> Ad-hoc sign all Mach-O files"

find "$APP_DST" -type f -print0 | while IFS= read -r -d '' file_path; do
  if file "$file_path" | grep -q "Mach-O"; then
    echo "SIGN: $file_path"
    chmod u+w "$file_path" || true
    codesign --remove-signature "$file_path" 2>/dev/null || true
    codesign --force --sign - --timestamp=none "$file_path"
  fi
done

echo "==> Ad-hoc sign app bundle"

codesign --remove-signature "$APP_DST" 2>/dev/null || true
codesign --force --sign - --timestamp=none "$APP_DST"

echo "==> Verify ad-hoc signature"

codesign --verify --verbose=4 "$APP_DST"

if ! codesign --verify --deep --strict --verbose=4 "$APP_DST"; then
  echo "WARN: deep strict verification failed. Printing diagnostics, but continuing."
  codesign --verify --deep --strict --verbose=4 "$APP_DST" || true
fi

echo "==> Check no duplicated Qt/Python in Frameworks"

if find "$APP_DST/Contents/Frameworks" -maxdepth 1 -type f \( -name "Qt*" -o -name "libQt*" -o -name "Python" -o -name "libpython*" \) | grep -q .; then
  echo "ERROR: duplicated Qt/Python libraries appeared after signing"
  find "$APP_DST/Contents/Frameworks" -maxdepth 1 -type f \( -name "Qt*" -o -name "libQt*" -o -name "Python" -o -name "libpython*" \)
  exit 1
fi

echo "==> Check no /opt/homebrew refs after cleanup"

bad_homebrew=0

while IFS= read -r macho; do
  if file "$macho" | grep -q "Mach-O"; then
    if otool -L "$macho" 2>/dev/null | grep -q "/opt/homebrew"; then
      echo "BAD HOMEBREW REF: $macho"
      otool -L "$macho" 2>/dev/null | grep "/opt/homebrew" || true
      bad_homebrew=1
    fi
  fi
done < <(find "$APP_DST" -type f -print)

if [ "$bad_homebrew" -eq 1 ]; then
  echo "ERROR: unresolved /opt/homebrew references remained"
  exit 1
fi

echo "==> Check final app structure"

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
  --scripts "$ROOT_DIR/ci/macos" \
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

FINAL_PKG="$ROOT_DIR/build/GorizontVS-VDI-Client-Setup-${APP_VERSION}-macos14-arm64.pkg"

productbuild \
  --product "$ROOT_DIR/build/product-requirements.plist" \
  --package "$ROOT_DIR/build/component.pkg" \
  "$FINAL_PKG"

echo "==> Done"

ls -lh "$FINAL_PKG"
