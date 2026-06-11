#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${1:?Usage: bundle_dylibs_spicy.sh /path/to/GorizontVS-VDI.app}"

APP_BIN_DIR="$APP_DIR/Contents/MacOS"
FRAMEWORKS_DIR="$APP_DIR/Contents/Frameworks"
SPICE_DIR="$APP_DIR/Contents/Resources/spice"

mkdir -p "$FRAMEWORKS_DIR"

is_system_lib() {
  local lib="$1"

  [[ "$lib" == /usr/lib/* ]] && return 0
  [[ "$lib" == /System/Library/* ]] && return 0

  return 1
}

is_macho() {
  file "$1" 2>/dev/null | grep -q "Mach-O"
}

resolve_rpath_lib() {
  local name="$1"

  for base in \
    "$APP_BIN_DIR" \
    "$FRAMEWORKS_DIR" \
    "$SPICE_DIR/lib" \
    "$SPICE_DIR/lib/gstreamer-1.0" \
    "/opt/homebrew/lib" \
    "/opt/homebrew/opt/python@3.13/Frameworks/Python.framework/Versions/3.13" \
    "/opt/homebrew/opt/openssl@3/lib" \
    "/opt/homebrew/opt/xz/lib" \
    "/opt/homebrew/opt/mpdecimal/lib" \
    "/opt/homebrew/opt/expat/lib" \
    "/opt/homebrew/opt/krb5/lib" \
    "/opt/homebrew/opt/cyrus-sasl/lib" \
    "/opt/homebrew/opt/gstreamer/lib" \
    "/opt/homebrew/opt/gst-plugins-base/lib" \
    "/opt/homebrew/opt/gst-plugins-good/lib" \
    "/opt/homebrew/opt/gst-plugins-bad/lib" \
    "/opt/homebrew/opt/gst-libav/lib" \
    "/opt/homebrew/opt/glib/lib" \
    "/opt/homebrew/opt/pixman/lib" \
    "/opt/homebrew/opt/phodav/lib" \
    "/opt/homebrew/opt/opus/lib" \
    "/opt/homebrew/opt/jpeg-turbo/lib" \
    "/opt/homebrew/opt/gettext/lib" \
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
    "/opt/homebrew/opt/jpeg-xl/lib" \
    "/opt/homebrew/opt/graphene/lib"
  do
    if [ -f "$base/$name" ]; then
      echo "$base/$name"
      return 0
    fi
  done

  return 1
}

resolve_dep() {
  local dep="$1"
  local loader_dir="$2"

  if [[ "$dep" == @loader_path/* ]]; then
    echo "$loader_dir/${dep#@loader_path/}"
    return
  fi

  if [[ "$dep" == @executable_path/* ]]; then
    echo "$APP_BIN_DIR/${dep#@executable_path/}"
    return
  fi

  if [[ "$dep" == @rpath/* ]]; then
    local name="${dep#@rpath/}"
    if resolve_rpath_lib "$name"; then
      return
    fi
  fi

  echo "$dep"
}

copy_lib() {
  local src="$1"

  [ -f "$src" ] || return 0

  local base
  base="$(basename "$src")"

  if [[ "$src" == *"/lib/gstreamer-1.0/"* ]]; then
    return 0
  fi

  if [[ "$base" == Qt* || "$base" == libQt* ]]; then
    echo "SKIP QT: $src"
    return 0
  fi

  if [[ "$base" == Python || "$base" == libpython* ]]; then
    echo "SKIP PYTHON: $src"
    return 0
  fi

  if [[ "$base" == libgtk-4* || "$base" == libgdk-4* ]]; then
    echo "SKIP GTK4: $src"
    return 0
  fi

  local dst="$FRAMEWORKS_DIR/$base"

  if [ ! -f "$dst" ]; then
    echo "COPY: $src -> $dst"
    cp -L "$src" "$dst"
    chmod u+w "$dst" || true
  fi
}

rewrite_dep() {
  local file_path="$1"
  local dep="$2"
  local dep_base
  dep_base="$(basename "$dep")"

  if [ "$dep_base" = "Python" ] && [ -f "$APP_BIN_DIR/Python" ]; then
    install_name_tool -change "$dep" "@rpath/Python" "$file_path" 2>/dev/null || true
    return 0
  fi

  if [ -f "$APP_BIN_DIR/$dep_base" ]; then
    install_name_tool -change "$dep" "@rpath/$dep_base" "$file_path" 2>/dev/null || true
    return 0
  fi

  if [ -f "$FRAMEWORKS_DIR/$dep_base" ]; then
    install_name_tool -change "$dep" "@rpath/$dep_base" "$file_path" 2>/dev/null || true
    return 0
  fi

  if [ -f "$SPICE_DIR/lib/$dep_base" ]; then
    install_name_tool -change "$dep" "@rpath/$dep_base" "$file_path" 2>/dev/null || true
    return 0
  fi

  if [ -f "$SPICE_DIR/lib/gstreamer-1.0/$dep_base" ]; then
    install_name_tool -change "$dep" "@rpath/$dep_base" "$file_path" 2>/dev/null || true
    return 0
  fi

  return 1
}

collect_macho_files() {
  find "$APP_DIR" -type f -print
}

echo "==> Collect dependencies"

changed=1
round=0

while [ "$changed" -eq 1 ] && [ "$round" -lt 40 ]; do
  changed=0
  round=$((round + 1))

  echo "scan round $round"

  while IFS= read -r f; do
    is_macho "$f" || continue

    loader_dir="$(dirname "$f")"

    while IFS= read -r line; do
      dep="$(echo "$line" | awk '{print $1}')"

      [ -n "$dep" ] || continue
      is_system_lib "$dep" && continue

      resolved="$(resolve_dep "$dep" "$loader_dir")"

      if [ -f "$resolved" ]; then
        before="$(find "$FRAMEWORKS_DIR" -type f | wc -l | tr -d ' ')"
        copy_lib "$resolved"
        after="$(find "$FRAMEWORKS_DIR" -type f | wc -l | tr -d ' ')"

        if [ "$before" != "$after" ]; then
          changed=1
        fi
      fi
    done < <(otool -L "$f" | tail -n +2 || true)
  done < <(collect_macho_files)
done

echo "==> Rewrite ids/rpaths/deps"

while IFS= read -r f; do
  is_macho "$f" || continue

  chmod u+w "$f" || true

  base="$(basename "$f")"

  case "$f" in
    *.dylib|*.so|*.bundle|"$APP_BIN_DIR"/Python|"$APP_BIN_DIR"/Qt*)
      install_name_tool -id "@rpath/$base" "$f" 2>/dev/null || true
      ;;
  esac

  install_name_tool -add_rpath "@loader_path" "$f" 2>/dev/null || true
  install_name_tool -add_rpath "@executable_path" "$f" 2>/dev/null || true

  install_name_tool -add_rpath "@loader_path/.." "$f" 2>/dev/null || true
  install_name_tool -add_rpath "@loader_path/../lib" "$f" 2>/dev/null || true
  install_name_tool -add_rpath "@loader_path/../Frameworks" "$f" 2>/dev/null || true
  install_name_tool -add_rpath "@loader_path/../../Frameworks" "$f" 2>/dev/null || true
  install_name_tool -add_rpath "@loader_path/../../../Frameworks" "$f" 2>/dev/null || true
  install_name_tool -add_rpath "@loader_path/../../../../Frameworks" "$f" 2>/dev/null || true

  install_name_tool -add_rpath "@executable_path/../lib" "$f" 2>/dev/null || true
  install_name_tool -add_rpath "@executable_path/../Frameworks" "$f" 2>/dev/null || true
  install_name_tool -add_rpath "@executable_path/../../../Frameworks" "$f" 2>/dev/null || true
  install_name_tool -add_rpath "@executable_path/../../../../Frameworks" "$f" 2>/dev/null || true

  while IFS= read -r line; do
    dep="$(echo "$line" | awk '{print $1}')"

    [ -n "$dep" ] || continue
    is_system_lib "$dep" && continue

    rewrite_dep "$f" "$dep" || true
  done < <(otool -L "$f" | tail -n +2 || true)
done < <(collect_macho_files)

echo "==> Validate no /opt/homebrew"

bad=0

while IFS= read -r f; do
  is_macho "$f" || continue

  if otool -L "$f" 2>/dev/null | grep -q "/opt/homebrew"; then
    echo "BAD HOMEBREW REF: $f"
    otool -L "$f" | grep "/opt/homebrew" || true
    bad=1
  fi
done < <(collect_macho_files)

if [ "$bad" -eq 1 ]; then
  echo "ERROR: unresolved /opt/homebrew dependencies found"
  exit 1
fi

echo "==> bundle_dylibs_spicy OK"
