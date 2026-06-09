from __future__ import annotations

import typing

from src.utils.resource_utils import read_text_resource


def _read_version() -> str:
    version = read_text_resource(":/meta/VERSION").strip()
    return version or "1.0"


APP_VERSION: typing.Final[str] = _read_version()
