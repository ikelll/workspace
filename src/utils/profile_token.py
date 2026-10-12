from __future__ import annotations

import base64
import binascii
import hashlib
import json
from dataclasses import dataclass

TOKEN_PREFIX = "GVS1"
TOKEN_VERSION = 1

_CHECKSUM_LENGTH = 8

_VALID_METHODS = ("password", "negotiate")


class ProfileTokenError(ValueError):
    def __init__(self, message: str, code: str = "invalid") -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ProfileTokenData:
    server_url: str
    auth_id: str
    auth_name: str = ""
    username: str = ""
    login_method: str = "password"
    spn: str = ""


def looks_like_profile_token(text: str) -> bool:
    return (text or "").strip().startswith(TOKEN_PREFIX + ".")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _checksum(payload_b64: str) -> str:
    return hashlib.sha256(payload_b64.encode("ascii")).hexdigest()[:_CHECKSUM_LENGTH]


def decode_profile_token(text: str) -> ProfileTokenData:
    token = (text or "").strip()
    token = "".join(token.split())
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != TOKEN_PREFIX:
        raise ProfileTokenError("not a profile token")

    _prefix, payload_b64, checksum = parts
    if not payload_b64 or not checksum:
        raise ProfileTokenError("token is incomplete")

    if _checksum(payload_b64) != checksum.lower():
        raise ProfileTokenError("token is corrupted or truncated")

    try:
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except (ValueError, binascii.Error, UnicodeDecodeError) as exc:
        raise ProfileTokenError("token payload is malformed") from exc

    if not isinstance(payload, dict):
        raise ProfileTokenError("token payload is malformed")

    if payload.get("v") != TOKEN_VERSION:
        raise ProfileTokenError("unsupported token version", code="version")

    server_url = str(payload.get("u", "") or "").strip().rstrip("/")
    auth_id = str(payload.get("a", "") or "").strip()
    if not server_url or not auth_id:
        raise ProfileTokenError("token payload is malformed")

    if "://" not in server_url:
        server_url = "https://" + server_url
    if not server_url.startswith(("http://", "https://")):
        raise ProfileTokenError("token payload is malformed")

    login_method = str(payload.get("m", "password") or "password").strip()
    if login_method not in _VALID_METHODS:
        login_method = "password"

    spn = str(payload.get("s", "") or "").strip()
    if login_method != "negotiate":
        spn = ""

    return ProfileTokenData(
        server_url=server_url,
        auth_id=auth_id,
        auth_name=str(payload.get("l", "") or "").strip(),
        username=str(payload.get("n", "") or "").strip(),
        login_method=login_method,
        spn=spn,
    )