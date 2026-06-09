from __future__ import annotations

import logging
import logging.handlers
import os
import re
import sys
from pathlib import Path

_LOG_FORMAT = "%(asctime)s [%(levelname)-7s] %(name)s (%(filename)s:%(lineno)d): %(message)s"
_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_MAX_BYTES = 5 * 1024 * 1024
_BACKUP_COUNT = 3
_LOG_FILENAME = "GorizontVSClient.log"
_APP_DIR_NAME = "GorizontVS"

_SENSITIVE_PATTERNS = re.compile(
    r"(password|passwd|token|scrambler|X-Auth-Token|Authorization)"
    r"[\s:=]+['\"]?([^\s'\",:}{)\]]+)",
    re.IGNORECASE,
)


def _app_log_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    log_dir = base / _APP_DIR_NAME / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


class _SensitiveFilter(logging.Filter):

    def filter(self, record: logging.LogRecord) -> bool:
        if record.args:
            try:
                record.msg = record.getMessage()
                record.args = None
            except Exception:
                pass
        if isinstance(record.msg, str):
            record.msg = _SENSITIVE_PATTERNS.sub(r"\1=<REDACTED>", record.msg)
        return True


def setup_logging() -> None:
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    if any(isinstance(h, logging.handlers.RotatingFileHandler) for h in root.handlers):
        return

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATE_FORMAT)
    sensitive_filter = _SensitiveFilter()

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)
    console.addFilter(sensitive_filter)
    root.addHandler(console)

    try:
        log_path = _app_log_dir() / _LOG_FILENAME
        file_handler = logging.handlers.RotatingFileHandler(
            str(log_path),
            maxBytes=_MAX_BYTES,
            backupCount=_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(sensitive_filter)
        root.addHandler(file_handler)
        root.info("Log file: %s", log_path)
    except Exception as exc:
        root.warning("Could not create file log handler: %s (falling back to console only)", exc)

    _install_exception_hook()


def _install_exception_hook() -> None:
    _original = sys.excepthook

    def _hook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            _original(exc_type, exc_value, exc_tb)
            return
        logging.getLogger("unhandled").critical(
            "Unhandled exception", exc_info=(exc_type, exc_value, exc_tb)
        )

    sys.excepthook = _hook
