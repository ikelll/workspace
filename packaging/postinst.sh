#!/bin/sh
set -e

DESKTOP="GorizontVS-VDI.desktop"
APPS_DIR="/usr/share/applications"
MIMEAPPS="/usr/share/applications/mimeapps.list"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APPS_DIR" || true
fi

mkdir -p "$(dirname "$MIMEAPPS")"
touch "$MIMEAPPS"

tmp="$(mktemp)"
awk '
  BEGIN{skip=0}
  /^\[Default Applications\]/{skip=1; print; next}
  /^\[/{skip=0; print; next}
  {
    if (skip==1 && ($0 ~ /^x-scheme-handler\/gorizontvs=/ \
                 || $0 ~ /^x-scheme-handler\/gorizontvss=/ \
                 || $0 ~ /^x-scheme-handler\/gorizontvsa=/)) next
    print
  }
' "$MIMEAPPS" > "$tmp"
cat "$tmp" > "$MIMEAPPS"
rm -f "$tmp"

if ! grep -q "^\[Default Applications\]" "$MIMEAPPS"; then
  printf "\n[Default Applications]\n" >> "$MIMEAPPS"
fi

printf "x-scheme-handler/gorizontvs=%s\n"  "$DESKTOP" >> "$MIMEAPPS"
printf "x-scheme-handler/gorizontvss=%s\n" "$DESKTOP" >> "$MIMEAPPS"
printf "x-scheme-handler/gorizontvsa=%s\n" "$DESKTOP" >> "$MIMEAPPS"

exit 0