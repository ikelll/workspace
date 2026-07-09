"""Общие фикстуры для тестов.

- Поднимает headless QCoreApplication (нужен многим модулям из-за QObject/Signal/QSettings).
- Если в окружении нет gssapi (например, на CI без Kerberos), подставляет лёгкую заглушку,
  чтобы модуль src.auth.negotiate можно было импортировать. Если настоящий gssapi есть —
  заглушка не ставится.
"""
from __future__ import annotations

import os
import sys
import types

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_app_dialogs_stub = types.ModuleType("src.dialogs.app_dialogs")
_app_dialogs_stub.confirm_certificate = lambda *a, **k: False  # type: ignore[attr-defined]
sys.modules["src.dialogs.app_dialogs"] = _app_dialogs_stub

if sys.platform != "win32":
    try:  # pragma: no cover
        import gssapi  # noqa: F401
    except Exception:  # pragma: no cover
        fake = types.ModuleType("gssapi")

        class _Credentials:  # noqa: D401
            def __init__(self, **_: object) -> None:
                raise RuntimeError("no kerberos credentials in test environment")

        fake.Credentials = _Credentials  # type: ignore[attr-defined]
        fake.Name = lambda *a, **k: object()  # type: ignore[attr-defined]
        fake.NameType = types.SimpleNamespace(hostbased_service=object())  # type: ignore[attr-defined]
        fake.SecurityContext = lambda *a, **k: object()  # type: ignore[attr-defined]
        fake.RequirementFlag = types.SimpleNamespace(  # type: ignore[attr-defined]
            mutual_authentication=1, delegate_to_peer=2
        )
        sys.modules["gssapi"] = fake

import pytest  # noqa: E402
from PySide6.QtCore import QCoreApplication  # noqa: E402  # type: ignore


@pytest.fixture(scope="session", autouse=True)
def _qapp():
    app = QCoreApplication.instance() or QCoreApplication([])
    yield app