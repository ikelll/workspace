from __future__ import annotations

import uuid
import hashlib
from dataclasses import dataclass, field

from PySide6.QtCore import QSettings # type: ignore

@dataclass
class Profile:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    server_url: str = ""
    auth_id: str = ""
    auth_name: str = ""
    username: str = ""
    login_method: str = "password"   # "password" | "negotiate"
    spn: str = ""

    @property
    def is_negotiate(self) -> bool:
        return self.login_method == "negotiate"

    @property
    def host(self) -> str:
        raw = self.server_url.split("://", 1)[-1].rstrip("/")
        return raw.split("/", 1)[0]

    @property
    def display_label(self) -> str:
        name = self.username or "?"
        return f"{name}@{self.host}"

    @property
    def initials(self) -> str:
        if self.username:
            parts = self.username.replace(".", " ").split()
            if len(parts) >= 2:
                return (parts[0][0] + parts[1][0]).upper()
            return self.username[0].upper()
        return "?"

_AVATAR_COLORS = [
    "#047394",  # teal (brand)
    "#0D9488",  # emerald
    "#7C3AED",  # violet
    "#DB2777",  # pink
    "#EA580C",  # orange
    "#CA8A04",  # amber
    "#16A34A",  # green
    "#2563EB",  # blue
]


def avatar_color(profile: Profile) -> str:
    key = profile.id or f"{profile.username}|{profile.server_url}|{profile.auth_id}"
    digest = hashlib.blake2b(key.encode("utf-8"), digest_size=4).digest()
    index = int.from_bytes(digest, "big") % len(_AVATAR_COLORS)
    return _AVATAR_COLORS[index]


_ARR = "profiles"
_LAST = "profiles_last_id"


class ProfileManager:

    def __init__(self, settings: QSettings) -> None:
        self._s = settings


    def load_all(self) -> list[Profile]:
        n = self._s.beginReadArray(_ARR)
        out: list[Profile] = []
        for i in range(n):
            self._s.setArrayIndex(i)
            out.append(Profile(
                id=str(self._s.value("id", "")),
                server_url=str(self._s.value("server_url", "")),
                auth_id=str(self._s.value("auth_id", "")),
                auth_name=str(self._s.value("auth_name", "")),
                username=str(self._s.value("username", "")),
                login_method=str(self._s.value("login_method", "password")),
                spn=str(self._s.value("spn", "")),
            ))
        self._s.endArray()
        return out

    def get_last_used_id(self) -> str | None:
        v = self._s.value(_LAST, None)
        return str(v) if v else None


    def _save_all(self, profiles: list[Profile]) -> None:
        self._s.beginWriteArray(_ARR, len(profiles))
        for i, p in enumerate(profiles):
            self._s.setArrayIndex(i)
            for k in ("id", "server_url", "auth_id", "auth_name", "username",
                       "login_method", "spn"):
                self._s.setValue(k, getattr(p, k))
        self._s.endArray()
        self._s.sync()

    def find_by_connection(self, server_url: str, auth_id: str) -> Profile | None:
        host = server_url.split("://", 1)[-1].rstrip("/").split("/", 1)[0].lower()
        for p in self.load_all():
            p_host = p.server_url.split("://", 1)[-1].rstrip("/").split("/", 1)[0].lower()
            if p_host == host and p.auth_id == auth_id:
                return p
        return None

    def add_or_update(self, profile: Profile) -> None:
        items = self.load_all()
        for i, p in enumerate(items):
            if p.id == profile.id:
                items[i] = profile
                break
        else:
            items.append(profile)
        self._save_all(items)
        self.set_last_used(profile.id)

    def delete(self, profile_id: str) -> None:
        items = [p for p in self.load_all() if p.id != profile_id]
        self._save_all(items)
        if self.get_last_used_id() == profile_id:
            self._s.remove(_LAST)
            self._s.sync()

    def set_last_used(self, profile_id: str) -> None:
        self._s.setValue(_LAST, profile_id)
        self._s.sync()
