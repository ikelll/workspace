from __future__ import annotations

import copy
import logging
import os
import shlex
from typing import Any

log = logging.getLogger(__name__)

DEFAULT_ALLOWED_CLIENTS: frozenset[str] = frozenset({
    "gorizont-spicy",
    "spicy",
    "gorizont-vs-x2go",
    "x2goclient",
})


class UnsafeTransportParams(ValueError):
    """Unsigned transport parameters request an unexpected executable."""


def _allowed_clients() -> frozenset[str]:
    extra = {
        item.strip().lower()
        for item in os.environ.get("GORIZONTVS_ALLOWED_CLIENTS", "").split(",")
        if item.strip()
    }
    return DEFAULT_ALLOWED_CLIENTS | extra


def _program_name(path: str) -> str:
    name = os.path.basename(str(path).replace("\\", "/")).strip().lower()
    for suffix in (".exe", ".bin"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name


def validate_transport_params(params: dict[str, Any]) -> None:
    raw_args = params.get("as_cmd") if isinstance(params, dict) else None
    if raw_args is None:
        return
    if not isinstance(raw_args, (list, tuple)) or not raw_args:
        raise UnsafeTransportParams("as_cmd must be a non-empty list")
    program = _program_name(str(raw_args[0]))
    if program not in _allowed_clients():
        raise UnsafeTransportParams(f"executable {program!r} is not allowed")


def _is_spice_transport(transport_type: str) -> bool:
    return "spice" in (transport_type or "").strip().lower()


def _remove_option(args: list[str], option: str) -> list[str]:
    result: list[str] = []
    skip_next = False
    prefix = f"{option}="

    for arg in args:
        if skip_next:
            skip_next = False
            continue
        if arg == option:
            skip_next = True
            continue
        if arg.startswith(prefix):
            continue
        result.append(arg)

    return result


def _apply_spice_options(params: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(params)
    raw_args = result.get("as_cmd")
    if not isinstance(raw_args, (list, tuple)) or not raw_args:
        log.warning("SPICE transport parameters do not contain a usable as_cmd list")
        return result

    args = [str(arg) for arg in raw_args]
    args = _remove_option(args, "--monitors")
    args = _remove_option(args, "--spice-shared-dir")

    multi_enabled = bool(settings.get("multi_monitor_enabled", False))
    try:
        count = int(settings.get("monitor_count", 1))
    except (TypeError, ValueError):
        count = 1
    count = max(1, min(4, count))
    if not multi_enabled:
        count = 1
    args.append(f"--monitors={count}")

    if bool(settings.get("webdav_enabled", False)):
        raw_path = str(settings.get("webdav_path", "") or "").strip()
        selected_path = (
            os.path.abspath(os.path.expanduser(raw_path)) if raw_path else ""
        )
        if selected_path and os.path.isdir(selected_path):
            args.append(f"--spice-shared-dir={selected_path}")
        elif selected_path:
            log.warning("Configured WebDAV directory does not exist: %s", selected_path)

    result["as_cmd"] = args
    result["as_cmd_str"] = " ".join(shlex.quote(arg) for arg in args)
    return result


def apply_client_transport_options(
    params: dict[str, Any],
    transport_type: str,
    client_settings: dict[str, Any] | None,
) -> dict[str, Any]:
    validate_transport_params(params)
    if not _is_spice_transport(transport_type):
        return copy.deepcopy(params)

    settings = client_settings or {}
    spice_settings = settings.get("spice", {})
    if not isinstance(spice_settings, dict):
        spice_settings = {}

    return _apply_spice_options(params, spice_settings)