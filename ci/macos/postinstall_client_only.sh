#!/bin/bash
set -e

APP="/Applications/GorizontVS-VDI.app"

if [ -d "$APP" ]; then
  /usr/bin/find "$APP" -type f -exec /usr/bin/xattr -c {} + 2>/dev/null || true
  /usr/bin/find "$APP" -type d -exec /usr/bin/xattr -c {} + 2>/dev/null || true
  /bin/chmod -R a+rX "$APP" || true

  if [ -f "$APP/Contents/MacOS/GorizontVS-VDI" ]; then
    /bin/chmod +x "$APP/Contents/MacOS/GorizontVS-VDI" || true
  fi
fi

exit 0
