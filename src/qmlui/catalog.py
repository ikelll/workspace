from __future__ import annotations

import hashlib
import re
from typing import Any, Iterable

from PySide6.QtCore import QCoreApplication, QSettings  # type: ignore

FAVORITES_KEY = "workspace/favorite_service_ids"
ACCENT_COUNT = 8



def status_kind(code: str, *, in_use: bool, maintenance: bool, not_accessible: bool) -> str:
    code = (code or "").strip().lower()
    if maintenance or code == "maintenance":
        return "warning"
    if not_accessible or code == "unavailable":
        return "danger"
    if in_use or code == "in_use":
        return "accent"
    if code in {"powering_on", "preparing", "rebooting", "powering_off"}:
        return "warning"
    if code == "off":
        return "neutral"
    return "success"


def status_title(svc: Any) -> str:
    code = str(getattr(svc, "status_code", "") or "").strip().lower()
    catalog = {
        "on": QCoreApplication.translate("Catalog", "Available"),
        "available": QCoreApplication.translate("Catalog", "Available"),
        "off": QCoreApplication.translate("Catalog", "Powered off"),
        "maintenance": QCoreApplication.translate("Catalog", "Maintenance"),
        "rebooting": QCoreApplication.translate("Catalog", "Rebooting"),
        "powering_on": QCoreApplication.translate("Catalog", "Powering on"),
        "powering_off": QCoreApplication.translate("Catalog", "Powering off"),
        "preparing": QCoreApplication.translate("Catalog", "Preparing"),
        "unavailable": QCoreApplication.translate("Catalog", "Unavailable"),
        "in_use": QCoreApplication.translate("Catalog", "In use"),
    }
    if code in catalog:
        return catalog[code]
    label = str(getattr(svc, "status_label", "") or "").strip()
    if label:
        return label
    if getattr(svc, "maintenance", False):
        return QCoreApplication.translate("Catalog", "Maintenance")
    if getattr(svc, "not_accessible", False):
        return QCoreApplication.translate("Catalog", "Unavailable")
    if getattr(svc, "in_use", False):
        return QCoreApplication.translate("Catalog", "In use")
    return QCoreApplication.translate("Catalog", "Available")


def _image_id(raw: object) -> str:
    value = str(raw or "").strip()
    return "" if value.lower() == "x" else value


OS_ARTWORK = {
    "windows_10": ("windows", "W"), "windows_11": ("windows", "W"), "windows_other": ("windows", "W"),
    "windows_server_2016": ("windows_server", "WS"), "windows_server_2019": ("windows_server", "WS"),
    "windows_server_2022": ("windows_server", "WS"), "windows_server_2025": ("windows_server", "WS"),
    "astra_linux": ("astra_linux", "A"), "redos": ("redos", "R"), "alt_linux": ("alt_linux", "ALT"),
    "rosa_linux": ("rosa_linux", "R"), "ubuntu": ("ubuntu", "U"), "debian": ("debian", "D"), "centos": ("centos", "C"),
    "rocky_linux": ("rocky_linux", "R"), "almalinux": ("almalinux", "A"), "fedora": ("fedora", "F"),
    "opensuse": ("opensuse", "S"), "linux_other": ("linux", "L"), "other": ("other", "OS"),
}
APP_ARTWORK = (
    (("excel",), ("excel", "X")), (("word",), ("word", "W")), (("photoshop",), ("photoshop", "Ps")),
    (("1c", "1с"), ("wave", "1C")), (("powerpoint",), ("powerpoint", "P")), (("outlook",), ("word", "O")),
    (("chrome", "firefox", "browser", "браузер", "yandex"), ("wave", "")), (("visual studio", "vs code", "vscode"), ("vscode", "VS")),
    (("postgres", "pgadmin"), ("postgres", "Pg")), (("autocad", "компас"), ("cad", "")), (("notepad",), ("wave", "N")),
)
APP_FALLBACKS = ("wave", "mint", "sand", "lilac")


def artwork_for(svc: Any, title: str, is_desktop: bool) -> tuple[str, str]:
    def initials(text: str) -> str:
        words = [w for w in re.split(r"[\s\-_:.]+", text.strip()) if w]
        if not words:
            return "?"
        if len(words) >= 2 and words[0][:1].isalpha() and words[1][:1].isalpha():
            return (words[0][0] + words[1][0]).upper()
        return words[0][:2].upper() if words[0][:2].isalpha() else words[0][:1].upper()

    if is_desktop:
        key = str(getattr(svc, "os_type", "") or "").strip().lower()
        if key in OS_ARTWORK:
            return OS_ARTWORK[key]
        family = str(getattr(svc, "os_family", "") or "").strip().lower()
        if family == "windows":
            return "windows", "W"
        if family == "linux":
            return "linux", "L"
        return "other", initials(title)
    lowered = title.lower()
    for keywords, (style, symbol) in APP_ARTWORK:
        if any(k in lowered for k in keywords):
            return style, symbol or initials(title)
    index = int.from_bytes(hashlib.blake2b(str(getattr(svc, "id", title)).encode("utf-8"), digest_size=1).digest(), "big")
    return APP_FALLBACKS[index % len(APP_FALLBACKS)], initials(title)


def accent_index(service_id: str) -> int:
    digest = hashlib.blake2b(str(service_id).encode("utf-8"), digest_size=2).digest()
    return int.from_bytes(digest, "big") % ACCENT_COUNT


def transport_label(transport: Any) -> str:
    name = str(getattr(transport, "name", "") or "").strip()
    transport_type = str(getattr(transport, "transport_type", "") or "").strip()
    if name and transport_type and name.lower() != transport_type.lower():
        return f"{name} · {transport_type}"
    return name or transport_type or QCoreApplication.translate("Catalog", "Transport")


def service_actions(svc: Any) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    if getattr(svc, "allow_poweron", False):
        actions.append({"id": "poweron", "title": QCoreApplication.translate("Catalog", "Power on"), "icon": "power"})
    if getattr(svc, "allow_poweroff", False):
        actions.append({"id": "poweroff", "title": QCoreApplication.translate("Catalog", "Power off"), "icon": "powerOff"})
    if getattr(svc, "allow_reset", False):
        actions.append({"id": "reset", "title": QCoreApplication.translate("Catalog", "Reset"), "icon": "refresh"})
    return actions


def service_to_dict(svc: Any, favorites: set[str]) -> dict[str, Any]:
    service_id = str(getattr(svc, "id", "") or "")
    transports = list(getattr(svc, "transports", []) or [])
    transports.sort(key=lambda t: getattr(t, "priority", 0))
    default = transports[0] if transports else None
    is_desktop = bool(getattr(svc, "is_desktop", False))
    group = getattr(svc, "group", None)
    group_name = str(getattr(group, "name", "") or "").strip()
    title = (str(getattr(svc, "visual_name", "") or "") or str(getattr(svc, "name", "") or "")).strip() or QCoreApplication.translate("Catalog", "Resource")
    code = str(getattr(svc, "status_code", "") or "").strip().lower()
    available = bool(getattr(svc, "is_available", True)) and bool(transports)
    artwork = artwork_for(svc, title, is_desktop)
    return {
        "id": service_id,
        "title": title,
        "name": str(getattr(svc, "name", "") or ""),
        "description": str(getattr(svc, "description", "") or "").strip(),
        "kind": "desktop" if is_desktop else "app",
        "kindTitle": QCoreApplication.translate("Catalog", "Desktop") if is_desktop else QCoreApplication.translate("Catalog", "Application"),
        "group": group_name,
        "imageId": _image_id(getattr(svc, "image_id", "")),
        "statusCode": code,
        "statusText": status_title(svc),
        "statusKind": status_kind(
            code,
            in_use=bool(getattr(svc, "in_use", False)),
            maintenance=bool(getattr(svc, "maintenance", False)),
            not_accessible=bool(getattr(svc, "not_accessible", False)),
        ),
        "statusDetail": str(getattr(svc, "status_detail", "") or ""),
        "available": available,
        "inUse": bool(getattr(svc, "in_use", False)),
        "customMessage": str(getattr(svc, "custom_message", "") or ""),
        "transports": [
            {
                "id": str(getattr(t, "id", "") or ""),
                "title": transport_label(t),
                "type": str(getattr(t, "transport_type", "") or ""),
                "isDefault": t is default,
            }
            for t in transports
        ],
        "showTransports": bool(getattr(svc, "show_transports", False)) or len(transports) > 1,
        "actions": service_actions(svc),
        "favorite": service_id in favorites,
        "accent": accent_index(service_id),
        "osType": str(getattr(svc, "os_type", "") or "").strip().lower(),
        "osTypeName": str(getattr(svc, "os_type_name", "") or "").strip(),
        "osFamily": str(getattr(svc, "os_family", "") or "").strip().lower(),
        "artwork": artwork[0],
        "symbol": artwork[1],
    }


def services_to_list(services: Iterable[Any], favorites: set[str]) -> list[dict[str, Any]]:
    items = [service_to_dict(svc, favorites) for svc in services]
    items.sort(key=lambda item: item["title"].lower())
    return items


class FavoritesStore:

    def __init__(self, settings: QSettings) -> None:
        self._settings = settings
        self._ids: set[str] = set(self._load())

    def _load(self) -> list[str]:
        raw = self._settings.value(FAVORITES_KEY, [])
        if raw is None:
            return []
        if isinstance(raw, str):
            return [raw] if raw else []
        return [str(v) for v in raw]

    @property
    def ids(self) -> set[str]:
        return set(self._ids)

    def contains(self, service_id: str) -> bool:
        return service_id in self._ids

    def toggle(self, service_id: str) -> bool:
        if service_id in self._ids:
            self._ids.discard(service_id)
            added = False
        else:
            self._ids.add(service_id)
            added = True
        self._settings.setValue(FAVORITES_KEY, sorted(self._ids))
        self._settings.sync()
        return added
