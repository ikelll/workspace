#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${1:?Usage: bundle_dylibs.sh /path/to/GorizontVS-VDI.app}"

APP_NAME="${APP_NAME:-GorizontVS-VDI}"

APP_BIN_DIR="$APP_DIR/Contents/MacOS"
FRAMEWORKS_DIR="$APP_DIR/Contents/Frameworks"
SPICE_DIR="$APP_DIR/Contents/Resources/spice"

MAIN_APP_BIN="$APP_BIN_DIR/$APP_NAME"

mkdir -p "$FRAMEWORKS_DIR"

is_system_lib() {
  local lib="$1"

  [[ "$lib" == /usr/lib/* ]] && return 0
  [[ "$lib" == /System/Library/* ]] && return 0

  return 1
}

is_macho() {
  local file_path="$1"
  file "$file_path" 2>/dev/null | grep -q "Mach-O"
}

resolve_lib() {
  local lib="$1"
  local loader_dir="$2"

  if [[ "$lib" == @loader_path/* ]]; then
    echo "$loader_dir/${lib#@loader_path/}"
    return
  fi

  if [[ "$lib" == @executable_path/* ]]; then
    echo "$APP_BIN_DIR/${lib#@executable_path/}"
    return
  fi

  if [[ "$lib" == @rpath/* ]]; then
    local name="${lib#@rpath/}"

    for base in \
      "$FRAMEWORKS_DIR" \
      "$SPICE_DIR/bin" \
      "$SPICE_DIR/lib" \
      "$SPICE_DIR/lib/gstreamer-1.0" \
      "/opt/homebrew/lib" \
      "/opt/homebrew/opt/gstreamer/lib" \
      "/opt/homebrew/opt/gstreamer/lib/gstreamer-1.0" \
      "/opt/homebrew/opt/gst-plugins-base/lib" \
      "/opt/homebrew/opt/gst-plugins-base/lib/gstreamer-1.0" \
      "/opt/homebrew/opt/gst-plugins-good/lib" \
      "/opt/homebrew/opt/gst-plugins-good/lib/gstreamer-1.0" \
      "/opt/homebrew/opt/gst-plugins-bad/lib" \
      "/opt/homebrew/opt/gst-plugins-bad/lib/gstreamer-1.0" \
      "/opt/homebrew/opt/gst-libav/lib" \
      "/opt/homebrew/opt/gst-libav/lib/gstreamer-1.0" \
      "/opt/homebrew/opt/openssl@3/lib" \
      "/opt/homebrew/opt/krb5/lib" \
      "/opt/homebrew/opt/cyrus-sasl/lib" \
      "/opt/homebrew/opt/jpeg-turbo/lib" \
      "/opt/homebrew/opt/gettext/lib" \
      "/opt/homebrew/opt/glib/lib" \
      "/opt/homebrew/opt/opus/lib" \
      "/opt/homebrew/opt/phodav/lib" \
      "/opt/homebrew/opt/pixman/lib" \
      "/opt/homebrew/opt/libusb/lib" \
      "/opt/homebrew/opt/ffmpeg/lib" \
      "/opt/homebrew/opt/x264/lib" \
      "/opt/homebrew/opt/x265/lib" \
      "/opt/homebrew/opt/aom/lib" \
      "/opt/homebrew/opt/dav1d/lib" \
      "/opt/homebrew/opt/libvpx/lib" \
      "/opt/homebrew/opt/svt-av1/lib" \
      "/opt/homebrew/opt/libogg/lib" \
      "/opt/homebrew/opt/libvorbis/lib" \
      "/opt/homebrew/opt/flac/lib" \
      "/opt/homebrew/opt/lame/lib" \
      "/opt/homebrew/opt/fdk-aac/lib" \
      "/opt/homebrew/opt/libass/lib" \
      "/opt/homebrew/opt/libpng/lib" \
      "/opt/homebrew/opt/webp/lib" \
      "/opt/homebrew/opt/jpeg-xl/lib"
    do
      if [ -f "$base/$name" ]; then
        echo "$base/$name"
        return
      fi
    done

    echo "$lib"
    return
  fi

  if [[ "$lib" == /opt/homebrew/* ]]; then
    local lib_base
    lib_base="$(basename "$lib")"

    for base in \
      "$(dirname "$lib")" \
      "/opt/homebrew/lib" \
      "/opt/homebrew/opt/gstreamer/lib" \
      "/opt/homebrew/opt/glib/lib" \
      "/opt/homebrew/opt/gettext/lib" \
      "/opt/homebrew/opt/openssl@3/lib" \
      "/opt/homebrew/opt/krb5/lib" \
      "/opt/homebrew/opt/cyrus-sasl/lib" \
      "/opt/homebrew/opt/jpeg-turbo/lib" \
      "/opt/homebrew/opt/opus/lib" \
      "/opt/homebrew/opt/phodav/lib" \
      "/opt/homebrew/opt/pixman/lib" \
      "/opt/homebrew/opt/libusb/lib" \
      "/opt/homebrew/opt/ffmpeg/lib" \
      "/opt/homebrew/opt/x264/lib" \
      "/opt/homebrew/opt/x265/lib" \
      "/opt/homebrew/opt/aom/lib" \
      "/opt/homebrew/opt/dav1d/lib" \
      "/opt/homebrew/opt/libvpx/lib" \
      "/opt/homebrew/opt/svt-av1/lib" \
      "/opt/homebrew/opt/libogg/lib" \
      "/opt/homebrew/opt/libvorbis/lib" \
      "/opt/homebrew/opt/flac/lib" \
      "/opt/homebrew/opt/lame/lib" \
      "/opt/homebrew/opt/fdk-aac/lib" \
      "/opt/homebrew/opt/libass/lib" \
      "/opt/homebrew/opt/libpng/lib" \
      "/opt/homebrew/opt/webp/lib" \
      "/opt/homebrew/opt/jpeg-xl/lib"
    do
      if [ -f "$base/$lib_base" ]; then
        echo "$base/$lib_base"
        return
      fi
    done

    found="$(
      find /opt/homebrew/opt /opt/homebrew/Cellar \
        -type f \
        -name "$lib_base" \
        2>/dev/null | head -n 1 || true
    )"

    if [ -n "$found" ] && [ -f "$found" ]; then
      echo "$found"
      return
    fi
  fi

  echo "$lib"
}

copy_lib() {
  local src="$1"

  [ -f "$src" ] || return 0

  local base
  base="$(basename "$src")"

  # GStreamer plugins already live in Resources/spice/lib/gstreamer-1.0.
  if [[ "$src" == *"/lib/gstreamer-1.0/"* ]]; then
    return 0
  fi

  # Do not duplicate Qt/Python from Nuitka/PySide runtime.
  if [[ "$base" == Qt* || "$base" == libQt* ]]; then
    echo "SKIP QT DUPLICATE: $src"
    return 0
  fi

  if [[ "$base" == Python || "$base" == libpython* ]]; then
    echo "SKIP PYTHON DUPLICATE: $src"
    return 0
  fi

  local dst="$FRAMEWORKS_DIR/$base"

  # ВАЖНО:
  # Перезаписываем уже существующую dylib, иначе может остаться старая
  # библиотека с install name /opt/homebrew/...
  if [ -f "$dst" ]; then
    echo "REPLACE EXISTING LIB: $dst <- $src"
    chmod u+w "$dst" || true
    rm -f "$dst"
  else
    echo "COPY: $src -> $dst"
  fi

  cp -L "$src" "$dst"
  chmod u+w "$dst" || true
}

collect_macho_files() {
  # ВАЖНО:
  # Обрабатываем только SPICE/GStreamer и скопированные dylib в Frameworks.
  # Основной Nuitka/PySide runtime в Contents/MacOS вообще не трогаем.
  {
    find "$SPICE_DIR" -type f -print
    find "$FRAMEWORKS_DIR" -type f -print
  } | sort -u
}

rewrite_dep_to_local() {
  local file_path="$1"
  local dep="$2"

  local dep_base
  dep_base="$(basename "$dep")"

  if [ -f "$FRAMEWORKS_DIR/$dep_base" ]; then
    install_name_tool -change "$dep" "@rpath/$dep_base" "$file_path" 2>/dev/null || true
  elif [ -f "$SPICE_DIR/bin/$dep_base" ]; then
    install_name_tool -change "$dep" "@rpath/$dep_base" "$file_path" 2>/dev/null || true
  elif [ -f "$SPICE_DIR/lib/$dep_base" ]; then
    install_name_tool -change "$dep" "@rpath/$dep_base" "$file_path" 2>/dev/null || true
  elif [ -f "$SPICE_DIR/lib/gstreamer-1.0/$dep_base" ]; then
    install_name_tool -change "$dep" "@rpath/$dep_base" "$file_path" 2>/dev/null || true
  else
    return 1
  fi
}

echo "==> Bundle dylib dependencies for SPICE + Frameworks only"
echo "APP_DIR=$APP_DIR"
echo "SPICE_DIR=$SPICE_DIR"
echo "FRAMEWORKS_DIR=$FRAMEWORKS_DIR"
echo "PROTECTED MAIN APP BIN=$MAIN_APP_BIN"

test -d "$SPICE_DIR"

changed=1
round=0

while [ "$changed" -eq 1 ] && [ "$round" -lt 30 ]; do
  changed=0
  round=$((round + 1))

  echo "==> Dependency scan round $round"

  while IFS= read -r file_path; do
    is_macho "$file_path" || continue

    loader_dir="$(dirname "$file_path")"

    while IFS= read -r line; do
      dep="$(echo "$line" | awk '{print $1}')"

      [ -n "$dep" ] || continue
      is_system_lib "$dep" && continue

      resolved="$(resolve_lib "$dep" "$loader_dir")"

      if [ -f "$resolved" ]; then
        before="$(find "$FRAMEWORKS_DIR" -type f | wc -l | tr -d ' ')"
        copy_lib "$resolved"
        after="$(find "$FRAMEWORKS_DIR" -type f | wc -l | tr -d ' ')"

        if [ "$before" != "$after" ]; then
          changed=1
        fi
      fi
    done < <(otool -L "$file_path" | tail -n +2 || true)
  done < <(collect_macho_files)
done

echo "==> Rewrite dylib paths and install names for SPICE + Frameworks only"

while IFS= read -r file_path; do
  is_macho "$file_path" || continue

  if [ "$file_path" = "$MAIN_APP_BIN" ]; then
    echo "ERROR: main app binary reached rewrite loop unexpectedly: $file_path"
    exit 1
  fi

  chmod u+w "$file_path" || true

  base="$(basename "$file_path")"

  case "$file_path" in
    *.dylib|*.so|*.bundle)
      install_name_tool -id "@rpath/$base" "$file_path" 2>/dev/null || true
      ;;
  esac

  # SPICE bin: Contents/Resources/spice/bin/spicy
  # @loader_path/../lib -> Contents/Resources/spice/lib
  install_name_tool -add_rpath "@loader_path/../lib" "$file_path" 2>/dev/null || true
  install_name_tool -add_rpath "@executable_path/../lib" "$file_path" 2>/dev/null || true

  # SPICE bin -> Contents/Frameworks
  # Contents/Resources/spice/bin -> ../../../Frameworks
  install_name_tool -add_rpath "@loader_path/../../../Frameworks" "$file_path" 2>/dev/null || true
  install_name_tool -add_rpath "@executable_path/../../../Frameworks" "$file_path" 2>/dev/null || true

  # GStreamer plugins:
  # Contents/Resources/spice/lib/gstreamer-1.0/plugin.dylib
  # @loader_path/.. -> Contents/Resources/spice/lib
  # @loader_path/../../../../Frameworks -> Contents/Frameworks
  install_name_tool -add_rpath "@loader_path/.." "$file_path" 2>/dev/null || true
  install_name_tool -add_rpath "@loader_path/../.." "$file_path" 2>/dev/null || true
  install_name_tool -add_rpath "@loader_path/../../../../Frameworks" "$file_path" 2>/dev/null || true
  install_name_tool -add_rpath "@executable_path/../../../../Frameworks" "$file_path" 2>/dev/null || true

  # Frameworks dylib -> same directory / app Frameworks
  install_name_tool -add_rpath "@loader_path" "$file_path" 2>/dev/null || true
  install_name_tool -add_rpath "@loader_path/." "$file_path" 2>/dev/null || true
  install_name_tool -add_rpath "@executable_path/../Frameworks" "$file_path" 2>/dev/null || true

  while IFS= read -r line; do
    dep="$(echo "$line" | awk '{print $1}')"

    [ -n "$dep" ] || continue
    is_system_lib "$dep" && continue

    rewrite_dep_to_local "$file_path" "$dep" || true
  done < <(otool -L "$file_path" | tail -n +2 || true)
done < <(collect_macho_files)

echo "==> Second rewrite pass for /opt/homebrew refs"

while IFS= read -r file_path; do
  is_macho "$file_path" || continue

  if [ "$file_path" = "$MAIN_APP_BIN" ]; then
    echo "ERROR: main app binary reached second rewrite loop unexpectedly: $file_path"
    exit 1
  fi

  chmod u+w "$file_path" || true

  while IFS= read -r line; do
    dep="$(echo "$line" | awk '{print $1}')"

    [ -n "$dep" ] || continue
    is_system_lib "$dep" && continue

    if [[ "$dep" == /opt/homebrew/* ]]; then
      if ! rewrite_dep_to_local "$file_path" "$dep"; then
        echo "WARN: cannot rewrite $dep in $file_path, local copy not found"
      fi
    fi
  done < <(otool -L "$file_path" | tail -n +2 || true)
done < <(collect_macho_files)

echo "==> Validate: no /opt/homebrew refs in SPICE + Frameworks"

bad=0

while IFS= read -r file_path; do
  is_macho "$file_path" || continue

  if [ "$file_path" = "$MAIN_APP_BIN" ]; then
    echo "ERROR: main app binary reached validation unexpectedly: $file_path"
    exit 1
  fi

  while IFS= read -r line; do
    dep="$(echo "$line" | awk '{print $1}')"

    if [[ "$dep" == /opt/homebrew/* ]]; then
      echo "BAD: $file_path still uses $dep"
      bad=1
    fi
  done < <(otool -L "$file_path" | tail -n +2 || true)
done < <(collect_macho_files)

if [ "$bad" -eq 1 ]; then
  echo "ERROR: unresolved /opt/homebrew dependencies found in SPICE/Frameworks"
  exit 1
fi

echo "==> Validate: main app binary was not renamed/touched"

if [ ! -x "$MAIN_APP_BIN" ]; then
  echo "ERROR: main app binary missing or not executable: $MAIN_APP_BIN"
  exit 1
fi

if [ -e "$APP_BIN_DIR/${APP_NAME}.real" ]; then
  echo "ERROR: unexpected wrapper real binary exists: $APP_BIN_DIR/${APP_NAME}.real"
  exit 1
fi

echo "==> Dylib bundle OK for SPICE + Frameworks only"
