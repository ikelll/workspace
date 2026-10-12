from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

pytest.importorskip("PySide6.QtCore")


def _load():
    spec = importlib.util.spec_from_file_location("build_client", ROOT / "tools" / "build_client.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


build = _load()


def _write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fake_qml_tree(root: Path) -> Path:
    qml = root / "qml"
    _write(qml / "builtins.qmltypes", "")
    _write(qml / "QtQml" / "qmldir", "module QtQml\nimport QtQml.Models auto\nimport QtQml.WorkerScript auto\n")
    _write(qml / "QtQml" / "Models" / "qmldir", "module QtQml.Models\n")
    _write(qml / "QtQml" / "WorkerScript" / "qmldir", "module QtQml.WorkerScript\n")
    _write(qml / "QtQml" / "XmlListModel" / "qmldir", "module QtQml.XmlListModel\n")
    _write(qml / "QtQuick" / "qmldir", "module QtQuick\nimport QtQml auto\n")
    _write(qml / "QtQuick" / "libqtquick2plugin.so", "")
    _write(qml / "QtQuick" / "Layouts" / "qmldir", "module QtQuick.Layouts\ndepends QtQuick auto\n")
    _write(qml / "QtQuick" / "Templates" / "qmldir", "module QtQuick.Templates\ndepends QtQuick auto\n")
    _write(qml / "QtQuick" / "Controls" / "qmldir",
           "module QtQuick.Controls\noptional import QtQuick.Controls.Fusion auto\n"
           "optional import QtQuick.Controls.Material auto\ndefault import QtQuick.Controls.Basic auto\n")
    _write(qml / "QtQuick" / "Controls" / "impl" / "qmldir", "module QtQuick.Controls.impl\ndepends QtQuick.Templates auto\n")
    _write(qml / "QtQuick" / "Controls" / "Basic" / "qmldir", "module QtQuick.Controls.Basic\ndepends QtQuick.Templates auto\n")
    _write(qml / "QtQuick" / "Controls" / "Basic" / "Button.qml", "import QtQuick\nimport QtQuick.Controls.impl\nimport QtQuick.Controls.Basic.impl\nItem {}\n")
    _write(qml / "QtQuick" / "Controls" / "Basic" / "impl" / "qmldir", "module QtQuick.Controls.Basic.impl\n")
    _write(qml / "QtQuick" / "Controls" / "Fusion" / "qmldir", "module QtQuick.Controls.Fusion\nimport QtQuick.Controls.Basic auto\n")
    _write(qml / "QtQuick" / "Controls" / "Fusion" / "Button.qml", "import QtQuick.Controls.Fusion.impl\nItem {}\n")
    _write(qml / "QtQuick" / "Controls" / "Fusion" / "impl" / "qmldir", "module QtQuick.Controls.Fusion.impl\n")
    _write(qml / "QtQuick" / "Controls" / "Material" / "qmldir", "module QtQuick.Controls.Material\n")
    _write(qml / "QtQuick" / "Controls" / "Material" / "Button.qml", "import QtQuick.Effects\nItem {}\n")
    _write(qml / "QtQuick" / "Controls" / "designer" / "x.qml", "")
    _write(qml / "QtQuick" / "Effects" / "qmldir", "module QtQuick.Effects\n")
    _write(qml / "QtQuick" / "Dialogs" / "qmldir", "module QtQuick.Dialogs\n")
    _write(qml / "QtWebEngine" / "qmldir", "module QtWebEngine\n")
    _write(qml / "QtWebEngine" / "libqtwebenginequickplugin.so", "")
    _write(qml / "Qt" / "labs" / "platform" / "qmldir", "module Qt.labs.platform\n")
    return qml


def _fake_app(root: Path) -> Path:
    app = root / "app"
    _write(app / "Main.qml", 'import QtQuick\nimport QtQuick.Controls\nimport QtQuick.Layouts\nimport "../Ui"\nItem {}\n')
    _write(app / "Ui" / "Theme.qml", "import QtQuick\nQtObject {}\n")
    return app


def test_needed_modules_follow_dependencies_but_not_optional_styles(tmp_path):
    qml, app = _fake_qml_tree(tmp_path), _fake_app(tmp_path)
    needed = build.needed_qml_modules(qml, app)
    assert needed == {
        "QtQml", "QtQml.Models", "QtQml.WorkerScript", "QtQuick", "QtQuick.Controls", "QtQuick.Controls.impl",
        "QtQuick.Controls.Basic", "QtQuick.Controls.Basic.impl", "QtQuick.Controls.Fusion",
        "QtQuick.Controls.Fusion.impl", "QtQuick.Layouts", "QtQuick.Templates",
    }


def test_prune_keeps_needed_modules_and_parents(tmp_path):
    qml, app = _fake_qml_tree(tmp_path), _fake_app(tmp_path)
    removed = build.prune_qml_dir(qml, build.needed_qml_modules(qml, app))
    removed_rel = {p.relative_to(qml).as_posix() for p in removed}
    assert removed_rel == {"Qt", "QtQml/XmlListModel", "QtQuick/Controls/Material", "QtQuick/Controls/designer",
                           "QtQuick/Dialogs", "QtQuick/Effects", "QtWebEngine"}
    assert (qml / "QtQuick" / "libqtquick2plugin.so").is_file()
    assert (qml / "QtQuick" / "Controls" / "Fusion" / "impl" / "qmldir").is_file()
    assert (qml / "builtins.qmltypes").is_file()
    assert not (qml / "QtWebEngine").exists()


def test_prune_dry_run_changes_nothing(tmp_path):
    qml, app = _fake_qml_tree(tmp_path), _fake_app(tmp_path)
    before = sorted(p.relative_to(qml).as_posix() for p in qml.rglob("*"))
    removed = build.prune_qml_dir(qml, build.needed_qml_modules(qml, app), dry_run=True)
    assert removed and sorted(p.relative_to(qml).as_posix() for p in qml.rglob("*")) == before


def test_prune_qt_plugins_removes_heavy_plugins_only(tmp_path):
    plugins = tmp_path / "plugins"
    for rel in ("imageformats/libqpdf.so", "imageformats/qpdf.dll", "imageformats/libqsvg.so", "platforms/libqxcb.so",
                "platforms/qwindows.dll", "platforms/libqvnc.so", "platforminputcontexts/libqtvirtualkeyboardplugin.so",
                "platforminputcontexts/libibusplatforminputcontextplugin.so", "tls/libqopensslbackend.so"):
        _write(plugins / rel, "")
    removed = {p.relative_to(plugins).as_posix() for p in build.prune_qt_plugins(plugins)}
    assert removed == {"imageformats/libqpdf.so", "imageformats/qpdf.dll", "platforms/libqvnc.so",
                       "platforminputcontexts/libqtvirtualkeyboardplugin.so"}
    assert (plugins / "platforms" / "libqxcb.so").is_file() and (plugins / "platforms" / "qwindows.dll").is_file()
    assert (plugins / "imageformats" / "libqsvg.so").is_file() and (plugins / "tls" / "libqopensslbackend.so").is_file()


def test_installed_pyside_covers_every_qml_import_of_the_client():
    paths = build.pyside_paths()
    needed = build.needed_qml_modules(paths["qml"], build.QML_SOURCES)
    for name in build.qml_imports_of(build.QML_SOURCES) | set(build.RUNTIME_QML_MODULES):
        assert name in needed, name
    assert "QtQuick.Controls.Material" not in needed and "QtWebEngine" not in needed


def test_nuitka_command_is_explicit_and_lean():
    command = build.nuitka_command("onefile", jobs=3, console=False, onefile_cache=False, version="2.0.0-abc1234")
    joined = " ".join(command)
    assert command[:3] == [sys.executable, "-m", "nuitka"]
    assert "--onefile" in command and "--enable-plugin=pyside6" in command and "--jobs=3" in command
    assert "--include-package=src" in command and "--include-package=resources" in command
    assert "--noinclude-qt-translations" in command and "--noinclude-qt-plugins=printsupport,egldeviceintegrations" in command
    assert "--file-version=2.0.0" in command and "--product-version=2.0.0" in command
    assert "--noinclude-dlls=*Qt6WebEngine*" in command and "--noinclude-dlls=*Qt6Quick3D*" in command
    assert "--include-data-dir" not in joined, "каталоги проекта в сборку как данные не попадают"
    assert "--include-qt-plugins=qml" not in joined, "QML-плагины Nuitka включает сама по импорту PySide6.QtQml"
    if sys.platform == "win32":
        assert "--windows-console-mode=attach" in command and "--output-filename=Gorizont-VS-VDI.exe" in command
    elif sys.platform == "darwin":
        assert "--macos-create-app-bundle" in command
    else:
        assert "--output-filename=Gorizont-VS-VDI.bin" in command and "--noinclude-dlls=libssl.so*" not in command
        assert "--onefile-cache-mode=cached" not in command
        cached = build.nuitka_command("onefile", jobs=1, console=False, onefile_cache=True, version="2.0.0",
                                      system_openssl=True)
        assert "--onefile-cache-mode=cached" in cached and "--noinclude-dlls=libssl.so*" in cached


def test_numeric_version():
    assert build.numeric_version("2.0.0-abc1234\n") == "2.0.0"
    assert build.numeric_version("v2.1") == "2.1"
    assert build.numeric_version("garbage") == "0.0.0"
