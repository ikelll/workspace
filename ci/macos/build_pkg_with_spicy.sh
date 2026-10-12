#!/usr/bin/env bash
set -euo pipefail

APP_NAME="${APP_NAME:-Gorizont-VS-VDI}"
APP_BUNDLE="${APP_BUNDLE:-Gorizont-VS-VDI.app}"
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

echo "==> Clean old package build outputs"
# Keep build/debug created by previous workflow steps.
rm -rf "$ROOT_DIR/build/pkgroot" \
       "$ROOT_DIR/build/component.plist" \
       "$ROOT_DIR/build/component.pkg"
rm -f "$ROOT_DIR/build"/Gorizont-VS-VDI-Client-Setup-*.pkg
mkdir -p "$ROOT_DIR/build/debug"

echo "==> Create clean payload"
mkdir -p "$PAYLOAD_DIR/Applications"

echo "==> Copy client app from dist"
cp -a "dist-mac/$APP_BUNDLE" "$PAYLOAD_DIR/Applications/"

test -d "$APP_DST"
test -x "$APP_MACOS_DIR/$APP_NAME"

echo "==> Prepare directories"
mkdir -p "$APP_FRAMEWORKS_DIR"
mkdir -p "$SPICE_DST/bin"
mkdir -p "$SPICE_DST/lib"
mkdir -p "$SPICE_DST/lib/gstreamer-1.0"
mkdir -p "$SPICE_DST/libexec/gstreamer-1.0"
mkdir -p "$SPICE_DST/share"
mkdir -p "$SPICE_DST/share/locale"
mkdir -p "$SPICE_DST/share/hwdata"

echo "==> Copy built SPICE prefix"

if [ ! -d "spice-full/build/spice/opt/homebrew" ]; then
  echo "ERROR: spice-full/build/spice/opt/homebrew not found"
  find spice-full/build/spice -maxdepth 8 -type d 2>/dev/null || true
  exit 1
fi

rsync -a "spice-full/build/spice/opt/homebrew/" "$SPICE_DST/"

test -x "$SPICE_DST/bin/gorizont-spicy"

echo "==> Copy usb.ids"

mkdir -p "$SPICE_DST/share/hwdata"

if [ -f "$ROOT_DIR/usb.ids" ]; then
  cp -f "$ROOT_DIR/usb.ids" "$SPICE_DST/share/hwdata/usb.ids"
elif [ -f "usb.ids" ]; then
  cp -f "usb.ids" "$SPICE_DST/share/hwdata/usb.ids"
elif [ -f "/opt/homebrew/share/hwdata/usb.ids" ]; then
  cp -f "/opt/homebrew/share/hwdata/usb.ids" "$SPICE_DST/share/hwdata/usb.ids"
else
  echo "WARNING: usb.ids not found"
fi

echo "==> Copy SPICE translations from /opt/homebrew output if exists"

if [ -d "spice-full/build/spice/opt/homebrew/share/locale" ]; then
  mkdir -p "$SPICE_DST/share/locale"
  rsync -a "spice-full/build/spice/opt/homebrew/share/locale/" "$SPICE_DST/share/locale/"
fi

echo "==> Copy custom SPICE translations from Makefile /usr output"

if [ -d "spice-full/build/spice/usr/share/locale" ]; then
  mkdir -p "$SPICE_DST/share/locale"
  rsync -a "spice-full/build/spice/usr/share/locale/" "$SPICE_DST/share/locale/"
fi

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

echo "==> Copy GTK/GLib/GStreamer/GdkPixbuf data"

for src in \
  "/opt/homebrew/share/gstreamer-1.0" \
  "/opt/homebrew/share/glib-2.0" \
  "/opt/homebrew/share/locale" \
  "/opt/homebrew/share/icons" \
  "/opt/homebrew/share/mime" \
  "/opt/homebrew/share/themes" \
  "/opt/homebrew/share/gtk-3.0" \
  "/opt/homebrew/share/gdk-pixbuf-2.0"
do
  if [ -d "$src" ]; then
    dst="$SPICE_DST/share/$(basename "$src")"
    mkdir -p "$dst"
    rsync -a "$src/" "$dst/"
  fi
done

echo "==> Re-copy usb.ids after Homebrew data copy"

mkdir -p "$SPICE_DST/share/hwdata"

if [ -f "$ROOT_DIR/usb.ids" ]; then
  cp -f "$ROOT_DIR/usb.ids" "$SPICE_DST/share/hwdata/usb.ids"
elif [ -f "usb.ids" ]; then
  cp -f "usb.ids" "$SPICE_DST/share/hwdata/usb.ids"
elif [ -f "/opt/homebrew/share/hwdata/usb.ids" ]; then
  cp -f "/opt/homebrew/share/hwdata/usb.ids" "$SPICE_DST/share/hwdata/usb.ids"
fi

echo "==> Re-copy custom SPICE translations after Homebrew locale copy"

if [ -d "spice-full/build/spice/opt/homebrew/share/locale" ]; then
  mkdir -p "$SPICE_DST/share/locale"
  rsync -a "spice-full/build/spice/opt/homebrew/share/locale/" "$SPICE_DST/share/locale/"
fi

if [ -d "spice-full/build/spice/usr/share/locale" ]; then
  mkdir -p "$SPICE_DST/share/locale"
  rsync -a "spice-full/build/spice/usr/share/locale/" "$SPICE_DST/share/locale/"
fi

echo "==> Verify custom Russian spice-gtk translation"

if [ -f "$SPICE_DST/share/locale/ru/LC_MESSAGES/gorizont-spice-gtk.mo" ]; then
  echo "OK: custom spice-gtk.mo bundled"
  ls -lh "$SPICE_DST/share/locale/ru/LC_MESSAGES/gorizont-spice-gtk.mo"
else
  echo "WARNING: custom gorizont-spice-gtk.mo not found"
  echo "Available locale files in spice build:"
  find spice-full/build/spice -path "*/share/locale/*" -type f | sort || true
fi

echo "==> Verify usb.ids"

if [ -f "$SPICE_DST/share/hwdata/usb.ids" ]; then
  echo "OK: usb.ids bundled"
  ls -lh "$SPICE_DST/share/hwdata/usb.ids"
else
  echo "WARNING: usb.ids not bundled"
fi

echo "==> Copy gdk-pixbuf loaders"

mkdir -p "$SPICE_DST/lib/gdk-pixbuf-2.0"

if [ -d "/opt/homebrew/lib/gdk-pixbuf-2.0" ]; then
  rsync -a "/opt/homebrew/lib/gdk-pixbuf-2.0/" "$SPICE_DST/lib/gdk-pixbuf-2.0/"
fi

if [ -d "/opt/homebrew/opt/gdk-pixbuf/lib/gdk-pixbuf-2.0" ]; then
  rsync -a "/opt/homebrew/opt/gdk-pixbuf/lib/gdk-pixbuf-2.0/" "$SPICE_DST/lib/gdk-pixbuf-2.0/"
fi

echo "==> Generate bundled gdk-pixbuf loaders.cache"

if [ -x "/opt/homebrew/bin/gdk-pixbuf-query-loaders" ]; then
  mkdir -p "$SPICE_DST/lib/gdk-pixbuf-2.0/2.10.0"

  if [ -d "$SPICE_DST/lib/gdk-pixbuf-2.0/2.10.0/loaders" ]; then
    "/opt/homebrew/bin/gdk-pixbuf-query-loaders" \
      "$SPICE_DST/lib/gdk-pixbuf-2.0/2.10.0/loaders/"*.so \
      > "$SPICE_DST/lib/gdk-pixbuf-2.0/2.10.0/loaders.cache" || true

    sed -i '' \
      "s#$SPICE_DST#/Applications/$APP_BUNDLE/Contents/Resources/spice#g" \
      "$SPICE_DST/lib/gdk-pixbuf-2.0/2.10.0/loaders.cache" || true
  fi
fi

echo "==> Bundle dylibs and fix rpaths"
ci/macos/bundle_dylibs_spicy.sh "$APP_DST"

echo "==> Remove duplicate/unwanted Frameworks libs"

rm -f "$APP_FRAMEWORKS_DIR"/Qt* || true
rm -f "$APP_FRAMEWORKS_DIR"/libQt* || true
rm -f "$APP_FRAMEWORKS_DIR"/Python || true
rm -f "$APP_FRAMEWORKS_DIR"/libpython* || true
rm -f "$APP_FRAMEWORKS_DIR"/libgtk-4*.dylib || true
rm -f "$APP_FRAMEWORKS_DIR"/libgdk-4*.dylib || true

echo "==> Remove invalid Contents/MacOS/spicy wrapper if exists"

rm -f "$APP_MACOS_DIR/spicy" || true

echo "==> Patch Info.plist"

PLIST="$APP_DST/Contents/Info.plist"

/usr/libexec/PlistBuddy -c "Set :LSMinimumSystemVersion $DEPLOY_TARGET" "$PLIST" 2>/dev/null || \
/usr/libexec/PlistBuddy -c "Add :LSMinimumSystemVersion string $DEPLOY_TARGET" "$PLIST"

/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $APP_VERSION" "$PLIST" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Set :CFBundleVersion $APP_VERSION" "$PLIST" 2>/dev/null || true

echo "==> Remove LSEnvironment from Info.plist if exists"

# Окружение теперь задаётся в macos_runtime.py.
# Не держим в Info.plist старые абсолютные пути и /Users/ruslan.
#/usr/libexec/PlistBuddy -c "Print :LSEnvironment" "$PLIST" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Delete :LSEnvironment" "$PLIST" 2>/dev/null || true

echo "==> Validate structure"

test -x "$APP_MACOS_DIR/$APP_NAME"
test -x "$SPICE_DST/bin/gorizont-spicy"
test -x "$SPICE_DST/libexec/gstreamer-1.0/gst-plugin-scanner"

if [ ! -f "$SPICE_DST/share/hwdata/usb.ids" ]; then
  echo "WARNING: $SPICE_DST/share/hwdata/usb.ids is missing"
fi

if [ ! -f "$SPICE_DST/share/locale/ru/LC_MESSAGES/gorizont-spice-gtk.mo" ]; then
  echo "WARNING: $SPICE_DST/share/locale/ru/LC_MESSAGES/gorizont-spice-gtk.mo is missing"
fi

echo "==> Permissions"

chmod -R u+w "$APP_DST" || true
chmod -R a+rX "$APP_DST"

chmod +x "$APP_MACOS_DIR/$APP_NAME"
chmod +x "$SPICE_DST/bin/gorizont-spicy"
chmod +x "$SPICE_DST/libexec/gstreamer-1.0/gst-plugin-scanner"

find "$SPICE_DST/bin" -type f -exec chmod +x {} + 2>/dev/null || true
find "$SPICE_DST/libexec" -type f -exec chmod +x {} + 2>/dev/null || true

echo "==> Remove stale signatures and extended attributes"

find "$APP_DST" -type d -name '_CodeSignature' -prune -exec rm -rf {} +
find "$APP_DST" -type l ! -exec test -e {} \; -print -delete
xattr -cr "$APP_DST" || true

echo "==> Remove Qt build artifacts"

QML_DIR="$APP_MACOS_DIR/PySide6/qml"
if [ -d "$QML_DIR" ]; then
  find "$QML_DIR" -type d \( -name 'objects-RelWithDebInfo' -o -name 'objects-Debug' -o -name 'objects-Release' \) -prune -exec rm -rf {} +
  find "$QML_DIR" -type f \( -name 'qmldir' -o -name '*.qmltypes' -o -name '*.qml' -o -name '*.js' \) -exec chmod a-x {} +
fi

echo "==> Relocate QML imports outside Contents/MacOS"

QML_SOURCE="$APP_MACOS_DIR/PySide6/qml"
QML_TARGET="$APP_RESOURCES_DIR/PySide6/qml"

if [ -d "$QML_SOURCE" ]; then
  mkdir -p "$(dirname "$QML_TARGET")"
  if [ -e "$QML_TARGET" ]; then
    echo "ERROR: QML target already exists: $QML_TARGET" >&2
    exit 1
  fi
  mv "$QML_SOURCE" "$QML_TARGET"
fi

if [ -d "$QML_TARGET" ]; then
  echo "==> Configure Qt QML import path"
  QT_CONF="$APP_RESOURCES_DIR/qt.conf"
  rm -f "$APP_MACOS_DIR/qt.conf"
  if [ -e "$QT_CONF" ]; then
    echo "ERROR: Existing Resources/qt.conf must be reconciled: $QT_CONF" >&2
    cat "$QT_CONF" >&2
    exit 1
  fi
  cat > "$QT_CONF" <<'QTCONF'
[Paths]
Prefix = .
QmlImports = PySide6/qml
Qml2Imports = PySide6/qml
QTCONF
fi

# Qt reads qt.conf from Contents/Resources for macOS application bundles.
# Keep text configuration out of Contents/MacOS to avoid codesign treating
# it as a nested code object.
if [ -e "$APP_MACOS_DIR/qt.conf" ]; then
  echo "ERROR: qt.conf remains in Contents/MacOS" >&2
  exit 1
fi

echo "==> Install native QML environment launcher"

ORIGINAL_EXECUTABLE="$APP_MACOS_DIR/$APP_NAME"
REAL_EXECUTABLE="$APP_MACOS_DIR/${APP_NAME}.bin"
LAUNCHER_SOURCE="$ROOT_DIR/build/debug/gorizont-qml-launcher.c"

if [ -e "$REAL_EXECUTABLE" ]; then
  echo "ERROR: launcher target already exists: $REAL_EXECUTABLE" >&2
  exit 1
fi

mv "$ORIGINAL_EXECUTABLE" "$REAL_EXECUTABLE"

cat > "$LAUNCHER_SOURCE" <<'C_SOURCE'
#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <mach-o/dyld.h>

int main(int argc, char **argv) {
    (void)argc;
    char executable[PATH_MAX];
    uint32_t size = sizeof(executable);
    if (_NSGetExecutablePath(executable, &size) != 0) {
        fprintf(stderr, "ERROR: executable path too long\n");
        return 1;
    }
    char *slash = strrchr(executable, '/');
    if (!slash) {
        fprintf(stderr, "ERROR: invalid executable path\n");
        return 1;
    }
    *slash = '\0';
    char qml[PATH_MAX];
    char target[PATH_MAX];
    if (snprintf(qml, sizeof(qml), "%s/../Resources/PySide6/qml", executable) >= (int)sizeof(qml) ||
        snprintf(target, sizeof(target), "%s/Gorizont-VS-VDI.bin", executable) >= (int)sizeof(target)) {
        fprintf(stderr, "ERROR: application path too long\n");
        return 1;
    }
    if (access(qml, R_OK) != 0 || access(target, X_OK) != 0) {
        fprintf(stderr, "ERROR: QML resources or application executable missing\n");
        return 1;
    }
    if (setenv("QML_IMPORT_PATH", qml, 1) != 0 ||
        setenv("QML2_IMPORT_PATH", qml, 1) != 0) {
        perror("setenv");
        return 1;
    }
    argv[0] = target;
    execv(target, argv);
    perror("execv");
    return 1;
}
C_SOURCE

clang -O2 -mmacosx-version-min="$DEPLOY_TARGET" \
  "$LAUNCHER_SOURCE" -o "$ORIGINAL_EXECUTABLE"
chmod +x "$ORIGINAL_EXECUTABLE" "$REAL_EXECUTABLE"

echo "==> Sign standalone Mach-O files"

is_framework_binary() {
  local path="$1" parent
  parent="$(dirname "$path")"
  while [ "$parent" != "$APP_DST" ] && [ "$parent" != '/' ]; do
    case "$parent" in
      *.framework|*.bundle|*.xpc|*.appex|*.app) return 0 ;;
    esac
    parent="$(dirname "$parent")"
  done
  return 1
}

while IFS= read -r -d '' f; do
  [ "$f" = "$APP_MACOS_DIR/$APP_NAME" ] && continue
  if file -b "$f" | grep -q 'Mach-O'; then
    if is_framework_binary "$f"; then
      continue
    fi
    echo "SIGN: $f"
    codesign --force --sign - --timestamp=none "$f"
  fi
done < <(find "$APP_DST" -type f -print0)

echo "==> Sign nested code bundles (deepest first)"

while IFS= read -r bundle; do
  echo "SIGN BUNDLE: $bundle"
  codesign --force --sign - --timestamp=none "$bundle"
done < <(
  find "$APP_DST" -type d \( -name '*.framework' -o -name '*.bundle' -o -name '*.xpc' -o -name '*.appex' -o -name '*.app' \)     ! -path "$APP_DST" -print | awk '{ print length($0), $0 }' | sort -rn | cut -d' ' -f2-
)

echo "==> Sign app bundle"
codesign --force --sign - --timestamp=none "$APP_DST"

echo "==> Verify app bundle"
codesign --verify --strict --verbose=4 "$APP_DST"

echo "==> Verify every Mach-O signature"
bad_sign=0
while IFS= read -r -d '' f; do
  if file -b "$f" | grep -q 'Mach-O'; then
    if ! codesign --verify --verbose=1 "$f" >/dev/null 2>&1; then
      echo "BAD SIGN: $f"
      bad_sign=1
    fi
  fi
done < <(find "$APP_DST" -type f -print0)

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

echo "==> Verify bundled locales"

find "$SPICE_DST/share/locale" -type f | sort || true

echo "==> Verify bundled hwdata"

find "$SPICE_DST/share/hwdata" -type f | sort || true

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

FINAL_PKG="$ROOT_DIR/build/Gorizont-VS-VDI-Client-Setup-${APP_VERSION}-arm64.pkg"

productbuild \
  --package "$ROOT_DIR/build/component.pkg" \
  "$FINAL_PKG"

echo "==> Done"

ls -lh "$FINAL_PKG"
