#!/bin/sh
set -e

MIMEAPPS="/usr/share/applications/mimeapps.list"

if [ -f "$MIMEAPPS" ]; then
  tmp="$(mktemp)"
  awk '
    BEGIN{in_def=0}
    /^\[Default Applications\]/{in_def=1; print; next}
    /^\[/{in_def=0; print; next}
    {
      if (in_def==1 && ($0 ~ /^x-scheme-handler\/gorizontvs=/ \
                     || $0 ~ /^x-scheme-handler\/gorizontvss=/ \
                     || $0 ~ /^x-scheme-handler\/gorizontvsa=/)) next
      print
    }
  ' "$MIMEAPPS" > "$tmp"
  cat "$tmp" > "$MIMEAPPS"
  rm -f "$tmp"
fi

exit 0