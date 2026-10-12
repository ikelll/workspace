from __future__ import annotations

import os
import re
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")

import pytest  # noqa: E402

pytest.importorskip("PySide6.QtQuick")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

QML_DIR = ROOT / "src" / "qmlui" / "qml"
QRC = ROOT / "resources" / "resource.qrc"


def _qrc_qml_entries() -> set[str]:
    text = QRC.read_text(encoding="utf-8")
    return set(re.findall(r'<file alias="([^"]+)">\.\./src/qmlui/qml/[^<]+</file>', text))


def test_every_qml_file_is_listed_in_qrc():
    on_disk = {p.relative_to(QML_DIR).as_posix() for p in QML_DIR.rglob("*") if p.is_file()}
    listed = _qrc_qml_entries()
    assert not (on_disk - listed), f"нет в resource.qrc: {sorted(on_disk - listed)}"
    assert not (listed - on_disk), f"в resource.qrc, но нет на диске: {sorted(listed - on_disk)}"


def test_compiled_resources_match_sources():
    import resources.rc_resource  # noqa: F401
    from PySide6.QtCore import QFile  # type: ignore

    for rel in sorted(_qrc_qml_entries()):
        source = (QML_DIR / rel).read_bytes()
        file = QFile(f":/qml/{rel}")
        assert file.open(QFile.OpenModeFlag.ReadOnly), rel
        assert bytes(file.readAll()) == source, f"rc_resource.py устарел для {rel} — запустите ./rebuild.sh"


def test_interface_loads_from_resources_only(monkeypatch, tmp_path):
    from PySide6.QtCore import QSettings, QUrl  # type: ignore
    from PySide6.QtWidgets import QApplication  # type: ignore

    import resources.rc_resource  # noqa: F401
    from src.qmlui import app as qml_app

    application = QApplication.instance() or QApplication([])
    qml_app.load_fonts(application)
    monkeypatch.setattr(qml_app, "main_qml_url", lambda: QUrl("qrc:/qml/Main.qml"))
    warnings: list[str] = []
    original = qml_app.QQmlApplicationEngine

    class Engine(original):
        def __init__(self, *args):
            super().__init__(*args)
            self.warnings.connect(lambda messages: warnings.extend(m.toString() for m in messages))

    monkeypatch.setattr(qml_app, "QQmlApplicationEngine", Engine)
    settings = QSettings(str(tmp_path / "client.ini"), QSettings.Format.IniFormat)
    engine, client = qml_app.create_engine(application, settings)
    try:
        assert engine.rootObjects(), warnings
        assert engine.rootObjects()[0].property("visible") is not None
        assert not warnings, warnings
    finally:
        import shiboken6
        engine.rootObjects()[0].close()
        client.shutdown()
        shiboken6.delete(engine)
