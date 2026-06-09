#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${1:?Usage: bundle_dylibs.sh /path/to/GorizontVS-VDI.app}"

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
      "$APP_BIN_DIR" \
      "$FRAMEWORKS_DIR" \
      "$SPICE_DIR/lib" \
      "$SPICE_DIR/lib/gstreamer-1.0" \
      "/opt/homebrew/lib" \
      "/opt/homebrew/opt/python@3.13/Frameworks/Python.framework/Versions/3.13" \
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
      "/opt/homebrew/opt/libusb/lib"
    do
      if [ -f "$base/$name" ]; then
        echo "$base/$name"
        return
      fi
    done

    echo "$lib"
    return
  fi

  echo "$lib"
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
    echo "SKIP QT DUPLICATE: $src"
    return 0
  fi

  if [[ "$base" == Python || "$base" == libpython* ]]; then
    echo "SKIP PYTHON DUPLICATE: $src"
    return 0
  fi

  local dst="$FRAMEWORKS_DIR/$base"

  if [ ! -f "$dst" ]; then
    echo "COPY: $src -> $dst"
    cp -L "$src" "$dst"
    chmod u+w "$dst" || true
  fi
}

collect_macho_files() {
  find "$APP_DIR" -type f -print
}

rewrite_dep_to_local() {
  local file_path="$1"
  local dep="$2"

  local dep_base
  dep_base="$(basename "$dep")"

  if [ -f "$APP_BIN_DIR/$dep_base" ]; then
    install_name_tool -change "$dep" "@rpath/$dep_base" "$file_path" 2>/dev/null || true
  elif [ -f "$FRAMEWORKS_DIR/$dep_base" ]; then
    install_name_tool -change "$dep" "@rpath/$dep_base" "$file_path" 2>/dev/null || true
  elif [ -f "$SPICE_DIR/lib/$dep_base" ]; then
    install_name_tool -change "$dep" "@rpath/$dep_base" "$file_path" 2>/dev/null || true
  elif [ -f "$SPICE_DIR/lib/gstreamer-1.0/$dep_base" ]; then
    install_name_tool -change "$dep" "@rpath/$dep_base" "$file_path" 2>/dev/null || true
  else
    return 1
  fi
}

echo "==> Collect dylib dependencies"

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

echo "==> Rewrite dylib paths and install names"

while IFS= read -r file_path; do
  is_macho "$file_path" || continue

  chmod u+w "$file_path" || true

  base="$(basename "$file_path")"

  case "$file_path" in
    *.dylib|*.so|*.bundle)
      install_name_tool -id "@rpath/$base" "$file_path" 2>/dev/null || true
      ;;
    "$APP_BIN_DIR"/Qt*|"$APP_BIN_DIR"/Python|"$FRAMEWORKS_DIR"/Qt*|"$FRAMEWORKS_DIR"/Python)
      install_name_tool -id "@rpath/$base" "$file_path" 2>/dev/null || true
      ;;
  esac

  install_name_tool -add_rpath "@executable_path/../Frameworks" "$file_path" 2>/dev/null || true
  install_name_tool -add_rpath "@executable_path" "$file_path" 2>/dev/null || true
  install_name_tool -add_rpath "@loader_path/../Frameworks" "$file_path" 2>/dev/null || true
  install_name_tool -add_rpath "@loader_path" "$file_path" 2>/dev/null || true
  install_name_tool -add_rpath "@loader_path/../../Frameworks" "$file_path" 2>/dev/null || true
  install_name_tool -add_rpath "@loader_path/.." "$file_path" 2>/dev/null || true

  while IFS= read -r line; do
    dep="$(echo "$line" | awk '{print $1}')"

    [ -n "$dep" ] || continue
    is_system_lib "$dep" && continue

    rewrite_dep_to_local "$file_path" "$dep" || true
  done < <(otool -L "$file_path" | tail -n +2 || true)
done < <(collect_macho_files)

echo "==> Second rewrite pass after install names changed"

while IFS= read -r file_path; do
  is_macho "$file_path" || continue

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

echo "==> Validate: no /opt/homebrew dylib references"

bad=0

while IFS= read -r file_path; do
  is_macho "$file_path" || continue

  while IFS= read -r line; do
    dep="$(echo "$line" | awk '{print $1}')"

    if [[ "$dep" == /opt/homebrew/* ]]; then
      echo "BAD: $file_path still uses $dep"
      bad=1
    fi
  done < <(otool -L "$file_path" | tail -n +2 || true)
done < <(collect_macho_files)

if [ "$bad" -eq 1 ]; then
  echo "ERROR: unresolved /opt/homebrew dependencies found"
  exit 1
fi

echo "==> Validate: no duplicated Qt/Python in Frameworks"

if find "$FRAMEWORKS_DIR" -maxdepth 1 -type f \( -name "Qt*" -o -name "libQt*" -o -name "Python" -o -name "libpython*" \) | grep -q .; then
  echo "ERROR: duplicated Qt/Python libraries found in Contents/Frameworks"
  find "$FRAMEWORKS_DIR" -maxdepth 1 -type f \( -name "Qt*" -o -name "libQt*" -o -name "Python" -o -name "libpython*" \)
  exit 1
fi

echo "==> Dylib bundle OK"
