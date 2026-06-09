from __future__ import annotations

from PySide6.QtCore import QFile  # type: ignore

import resources.rc_resource as _rc_resource  # noqa: F401


def read_text_resource(path: str, encoding: str = "utf-8") -> str:
    file = QFile(path)
    if not file.open(QFile.ReadOnly | QFile.Text):
        return ""

    try:
        data = file.readAll()
        return bytes(data).decode(encoding)
    finally:
        file.close()
