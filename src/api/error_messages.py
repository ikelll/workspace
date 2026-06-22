from __future__ import annotations

import re
from typing import Any

from PySide6.QtCore import QCoreApplication  # type: ignore


_WS_RE = re.compile(r"\s+")


def _normalize(value: Any) -> str:
    return _WS_RE.sub(" ", str(value or "").strip()).lower()


def translate_server_message(message: Any) -> str:

    raw = str(message or "").strip()
    if not raw:
        return QCoreApplication.translate("AuthService", "Unexpected server response")

    normalized = _normalize(raw)

    if normalized == "invalid credentials":
        return QCoreApplication.translate("AuthService", "Invalid username or password")

    if normalized in {
        "the requested service is in maintenance mode",
        "requested service is in maintenance mode",
        "service is in maintenance mode",
    }:
        return QCoreApplication.translate("ServiceInfo", "This service is in maintenance mode")

    if normalized in {"service is not accessible", "not_accesible"}:
        return QCoreApplication.translate("ServiceInfo", "Unavailable")
    
    if normalized in {"service is in preparation", "service in preparation"}:
        return QCoreApplication.translate(
            "ServiceInfo",
            "The machine is being prepared. Please try again shortly.",
        )


    if normalized in {
        "max services reached",
        "maxservicesreachederror",
        "maximum services reached",
        "maximum number of services has been reached",
        "number of maximum services has been reached",
    }:
        return QCoreApplication.translate(
            "ServiceInfo",
            "The maximum number of available machines has been reached. Contact your administrator.",
        )

    if normalized == "this transport requires a password-backed session":
        return QCoreApplication.translate(
            "ServiceInfo",
            "This transport requires a password. Sign in with a password and try again.",
        )
    if normalized in {"session expired", "invalid session", "unauthorized"}:
        return QCoreApplication.translate(
            "AppWidget",
            "Session expired. Please sign in again.",
        )

    return raw