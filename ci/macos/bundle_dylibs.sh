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
      "$SPICE_DIR/lib" \
      "/opt/homebrew/lib" \
      "/opt/homebrew/opt/openssl@3/lib" \
      "/opt/homebrew/opt/krb5/lib" \
      "/opt/homebrew/opt/cyrus-sasl/lib" \
      "/opt/homebrew/opt/jpeg-turbo/lib" \
      "/opt/homebrew/opt/gettext/lib"
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

  local dst="$FRAMEWORKS_DIR/$base"

  if [ ! -f "$dst" ]; then
    echo "COPY: $src -> $dst"
    cp -L "$src" "$dst"
    chmod u+w "$dst" || true
  fi
}

collect_macho_files() {
  find "$APP_DIR" -type f \( \
    -perm -111 \
    -o -name "*.dylib" \
    -o -name "*.so" \
    -o -name "*.bundle" \
  \) -print
}

echo "==> Collect dylib dependencies"

changed=1
round=0

while [ "$changed" -eq 1 ] && [ "$round" -lt 30 ]; do
  changed=0
  round=$((round + 1))

  echo "==> Dependency scan round $round"

  while IFS= read -r file; do
    file "$file" | grep -q "Mach-O" || continue

    loader_dir="$(dirname "$file")"

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
    done < <(otool -L "$file" | tail -n +2 || true)
  done < <(collect_macho_files)
done

echo "==> Rewrite dylib paths"

while IFS= read -r file; do
  file "$file" | grep -q "Mach-O" || continue

  chmod u+w "$file" || true

  base="$(basename "$file")"

  if [[ "$file" == "$FRAMEWORKS_DIR/"* ]]; then
    install_name_tool -id "@rpath/$base" "$file" 2>/dev/null || true
  fi

  loader_dir="$(dirname "$file")"

  install_name_tool -add_rpath "@executable_path/../Frameworks" "$file" 2>/dev/null || true
  install_name_tool -add_rpath "@loader_path/../Frameworks" "$file" 2>/dev/null || true
  install_name_tool -add_rpath "@loader_path" "$file" 2>/dev/null || true

  while IFS= read -r line; do
    dep="$(echo "$line" | awk '{print $1}')"

    [ -n "$dep" ] || continue
    is_system_lib "$dep" && continue

    resolved="$(resolve_lib "$dep" "$loader_dir")"

    if [ -f "$resolved" ]; then
      dep_base="$(basename "$resolved")"

      if [ -f "$FRAMEWORKS_DIR/$dep_base" ]; then
        install_name_tool -change "$dep" "@rpath/$dep_base" "$file" 2>/dev/null || true
      fi
    fi
  done < <(otool -L "$file" | tail -n +2 || true)
done < <(collect_macho_files)

echo "==> Validate: no /opt/homebrew dylib references"

bad=0

while IFS= read -r file; do
  file "$file" | grep -q "Mach-O" || continue

  while IFS= read -r line; do
    dep="$(echo "$line" | awk '{print $1}')"

    if [[ "$dep" == /opt/homebrew/* ]]; then
      echo "BAD: $file still uses $dep"
      bad=1
    fi
  done < <(otool -L "$file" | tail -n +2 || true)
done < <(collect_macho_files)

if [ "$bad" -eq 1 ]; then
  echo "ERROR: unresolved /opt/homebrew dependencies found"
  exit 1
fi

echo "==> Dylib bundle OK"
