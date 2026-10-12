from __future__ import annotations

import os
import sys
import tempfile
import types

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_ISOLATED_HOME = tempfile.mkdtemp(prefix="gvs-tests-")
os.environ["XDG_CONFIG_HOME"] = os.path.join(_ISOLATED_HOME, "config")
os.environ["XDG_DATA_HOME"] = os.path.join(_ISOLATED_HOME, "data")
os.environ["LOCALAPPDATA"] = os.path.join(_ISOLATED_HOME, "localappdata")
os.environ["GORIZONTVS_MULTI_INSTANCE"] = "1"

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
from PySide6.QtCore import QCoreApplication, QSettings  # noqa: E402  # type: ignore

QSettings.setDefaultFormat(QSettings.Format.IniFormat)
for _fmt in (QSettings.Format.NativeFormat, QSettings.Format.IniFormat):
    QSettings.setPath(_fmt, QSettings.Scope.UserScope, os.path.join(_ISOLATED_HOME, "settings"))
    QSettings.setPath(_fmt, QSettings.Scope.SystemScope, os.path.join(_ISOLATED_HOME, "settings-system"))


@pytest.fixture(autouse=True)
def _clean_trust_store():
    settings = QSettings("Gorizont-VS", "VDIClient")
    settings.remove("ssl")
    settings.sync()
    yield


@pytest.fixture(scope="session", autouse=True)
def _qapp():
    try:
        from PySide6.QtWidgets import QApplication  # type: ignore
        app = QCoreApplication.instance() or QApplication([])
    except Exception:  # pragma: no cover
        app = QCoreApplication.instance() or QCoreApplication([])
    yield app