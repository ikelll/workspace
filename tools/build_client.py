#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

ROOT = Path(__file__).resolve().parents[1]
APP_NAME = "Gorizont-VS-VDI"
MAIN_FILE = ROOT / "Gorizont-VS-VDI.py"
QML_SOURCES = ROOT / "src" / "qmlui" / "qml"
BUILD_DIR = ROOT / "deployment"       

IS_WINDOWS = sys.platform == "win32"
IS_MACOS = sys.platform == "darwin"
IS_LINUX = not IS_WINDOWS and not IS_MACOS

RUNTIME_QML_MODULES = ("QtQuick.Controls.Fusion", "QtQuick.Controls.Basic")

QT_PLUGIN_FAMILIES_EXCLUDED = ("printsupport", "egldeviceintegrations")
QT_PLUGIN_FAMILIES_EXTRA_LINUX = ("platforminputcontexts",)  

QT_PLUGIN_FILES_EXCLUDED = (
    "imageformats/*qpdf*",
    "platforminputcontexts/*virtualkeyboard*",
    "platforms/*qeglfs*",
    "platforms/*qlinuxfb*",
    "platforms/*qminimalegl*",
    "platforms/*qvkkhrdisplay*",
    "platforms/*qvnc*",
    "platforms/*qdirect2d*",
)

QT_LIBS_EXCLUDED = (
    "*Qt6Pdf*", "*Qt6VirtualKeyboard*", "*Qt6WebEngine*", "*Qt6WebView*", "*Qt6Multimedia*",
    "*Qt6Quick3D*", "*Qt63D*", "*Qt6Charts*", "*Qt6DataVisualization*", "*Qt6Graphs*",
    "*Qt6Location*", "*Qt6Positioning*", "*Qt6Sensors*", "*Qt6RemoteObjects*", "*Qt6Scxml*",
    "*Qt6TextToSpeech*", "*Qt6WebSockets*", "*Qt6WebChannel*", "*Qt6Core5Compat*", "*Qt6Designer*",
    "*Qt6ShaderTools*", "*Qt6QuickControls2Material*", "*Qt6QuickControls2Universal*",
    "*Qt6QuickControls2Imagine*", "*Qt6QuickControls2FluentWinUI3*", "*Qt6LabsStyleKit*",
    "*libav*", "*libsw*", "*avcodec*", "*avformat*", "*avutil*", "*swresample*", "*swscale*",
)

IMPORT_RE = re.compile(r"^\s*import\s+([A-Za-z_][\w.]*)", re.M)


def log(message: str) -> None:
    print("[build] " + message, flush=True)


def run(command: List[str], **kwargs) -> None:
    log("$ " + " ".join(_quote(part) for part in command))
    subprocess.run(command, check=True, **kwargs)


def _quote(value: str) -> str:
    return '"%s"' % value if " " in value else value


def tool(name: str) -> str:
    scripts_dir = Path(sys.executable).parent
    for candidate in (scripts_dir / (name + ".exe"), scripts_dir / name):
        if candidate.is_file():
            return str(candidate)
    found = shutil.which(name)
    if found:
        return found
    raise SystemExit("[build] не найден %s — установите PySide6 в этот venv (%s)" % (name, sys.executable))


def optional_packages(names: Iterable[str]) -> List[str]:
    result: List[str] = []
    for name in names:
        try:
            spec = importlib.util.find_spec(name)
        except (ImportError, ValueError):
            spec = None
        if spec is None:
            log("предупреждение: пакет %s не установлен в %s — в сборку не попадёт" % (name, sys.executable))
        elif spec.submodule_search_locations:
            result.append("--include-package=" + name)
        else:
            result.append("--include-module=" + name)
    return result


def numeric_version(raw: str) -> str:
    match = re.match(r"\s*v?(\d+(?:\.\d+){0,3})", raw)
    return match.group(1) if match else "0.0.0"


def read_version() -> str:
    try:
        return (ROOT / "VERSION").read_text(encoding="utf-8").strip() or "0.0.0"
    except OSError:
        return "0.0.0"


def pyside_paths() -> Dict[str, Path]:
    import PySide6  # noqa: WPS433  (импорт из venv сборки)
    from PySide6.QtCore import QLibraryInfo  # type: ignore

    package = Path(PySide6.__file__).resolve().parent
    try:
        location = QLibraryInfo.LibraryPath
        qml = Path(QLibraryInfo.path(location.QmlImportsPath))
        plugins = Path(QLibraryInfo.path(location.PluginsPath))
    except AttributeError: 
        qml = Path(QLibraryInfo.location(QLibraryInfo.Qml2ImportsPath))  # type: ignore[attr-defined]
        plugins = Path(QLibraryInfo.location(QLibraryInfo.PluginsPath))  # type: ignore[attr-defined]
    if not qml.is_dir():
        qml = package / "Qt" / "qml" if (package / "Qt" / "qml").is_dir() else package / "qml"
    if not plugins.is_dir():
        plugins = package / "Qt" / "plugins" if (package / "Qt" / "plugins").is_dir() else package / "plugins"
    return {"package": package, "qml": qml, "plugins": plugins, "version": PySide6.__version__}


def qml_imports_of(sources: Path) -> Set[str]:
    names: Set[str] = set()
    for path in list(sources.rglob("*.qml")) + list(sources.rglob("*.js")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        names.update(IMPORT_RE.findall(text))
    return names


def module_dir(qml_root: Path, name: str) -> Optional[Path]:
    path = qml_root.joinpath(*name.split("."))
    return path if (path / "qmldir").is_file() else None


def module_dependencies(qml_root: Path, name: str) -> Set[str]:
    directory = module_dir(qml_root, name)
    result: Set[str] = set()
    if directory is None:
        return result
    for line in (directory / "qmldir").read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] in ("import", "depends"):
            result.add(parts[1])
        elif len(parts) >= 3 and parts[0] == "default" and parts[1] == "import":
            result.add(parts[2])
    for path in list(directory.glob("*.qml")) + list(directory.glob("*.js")):
        result.update(IMPORT_RE.findall(path.read_text(encoding="utf-8", errors="replace")))
    return result


def needed_qml_modules(qml_root: Path, sources: Path, extra: Iterable[str] = RUNTIME_QML_MODULES) -> Set[str]:
    todo = list(qml_imports_of(sources) | set(extra))
    seen: Set[str] = set()
    while todo:
        name = todo.pop()
        if name in seen:
            continue
        seen.add(name)
        todo.extend(dep for dep in module_dependencies(qml_root, name) if dep not in seen)
    return {name for name in seen if module_dir(qml_root, name) is not None}


def prune_qml_dir(qml_root: Path, keep_modules: Iterable[str], dry_run: bool = False) -> List[Path]:
    keep = {Path(*name.split(".")).as_posix() for name in keep_modules}
    removed: List[Path] = []

    def visit(directory: Path) -> None:
        for entry in sorted(directory.iterdir()):
            if not entry.is_dir():
                continue
            rel = entry.relative_to(qml_root).as_posix()
            if rel in keep or any(k.startswith(rel + "/") for k in keep):
                visit(entry)     
                continue
            removed.append(entry)
            if not dry_run:
                shutil.rmtree(entry)

    visit(qml_root)
    return removed


def prune_qt_plugins(plugins_root: Path, dry_run: bool = False) -> List[Path]:
    removed: List[Path] = []
    for pattern in QT_PLUGIN_FILES_EXCLUDED:
        for path in plugins_root.glob(pattern):
            removed.append(path)
            if not dry_run:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
    return removed


def prune_pyside(paths: Dict[str, Path], dry_run: bool) -> None:
    qml_root, plugins_root = paths["qml"], paths["plugins"]
    app_imports = qml_imports_of(QML_SOURCES)
    keep = needed_qml_modules(qml_root, QML_SOURCES)
    missing = sorted(name for name in app_imports if module_dir(qml_root, name) is None
                     and name.split(".")[0].startswith("Qt"))
    if missing:
        raise SystemExit("[build] в установленном PySide6 нет QML-модулей, нужных клиенту: %s" % ", ".join(missing))
    log("QML-модули, которые остаются (%d): %s" % (len(keep), ", ".join(sorted(keep))))
    removed = prune_qml_dir(qml_root, keep, dry_run=dry_run)
    log("%s QML-модулей/каталогов: %d (%s)" % ("удалено" if not dry_run else "будет удалено", len(removed),
        ", ".join(p.relative_to(qml_root).as_posix() for p in removed[:12]) + (", …" if len(removed) > 12 else "")))
    removed_plugins = prune_qt_plugins(plugins_root, dry_run=dry_run)
    log("%s плагинов Qt: %s" % ("удалено" if not dry_run else "будет удалено",
        ", ".join(p.relative_to(plugins_root).as_posix() for p in removed_plugins) or "—"))


def rebuild_resources() -> None:
    i18n = ROOT / "i18n"
    for ts in sorted(i18n.glob("*.ts")):
        run([tool("pyside6-lrelease"), str(ts), "-qm", str(ts.with_suffix(".qm"))])
    run([tool("pyside6-rcc"), str(ROOT / "resources" / "resource.qrc"), "-o", str(ROOT / "resources" / "rc_resource.py")])


def nuitka_command(mode: str, jobs: int, console: bool, onefile_cache: bool, version: str,
                   system_openssl: bool = False) -> List[str]:
    numeric = numeric_version(version)
    command = [
        sys.executable, "-m", "nuitka", str(MAIN_FILE),
        "--" + mode,
        "--enable-plugin=pyside6",
        "--assume-yes-for-downloads",
        "--jobs=%d" % max(1, jobs),
        "--output-dir=" + str(BUILD_DIR),
        "--noinclude-qt-translations",
        "--noinclude-qt-plugins=" + ",".join(QT_PLUGIN_FAMILIES_EXCLUDED),
        "--include-package=src",
        "--include-package=resources",
        "--include-module=PySide6.QtSvg",
        "--company-name=Gorizont-VS",
        "--product-name=Gorizont-VS VDI Client",
        "--file-version=" + numeric,
        "--product-version=" + numeric,
        "--file-description=Gorizont-VS VDI Client",
        "--copyright=Gorizont-VS",
    ]
   
    command += optional_packages(("spnego",) + (("sspilib", "win32api", "win32crypt", "win32security", "win32con")
                                               if IS_WINDOWS else ("gssapi", "krb5")))
    command += ["--noinclude-dlls=*.cpp.o", "--noinclude-dlls=*.o", "--noinclude-dlls=*.qsb"]
    command += ["--noinclude-dlls=" + pattern for pattern in QT_LIBS_EXCLUDED]

    if IS_LINUX:
        command += ["--include-qt-plugins=" + ",".join(QT_PLUGIN_FAMILIES_EXTRA_LINUX)]
        if system_openssl:
            command += ["--noinclude-dlls=libssl.so*", "--noinclude-dlls=libcrypto.so*"]
        if mode == "onefile":
            command += ["--output-filename=%s.bin" % APP_NAME]
            if onefile_cache:
                command += ["--onefile-cache-mode=cached",
                            "--onefile-tempdir-spec={CACHE_DIR}/%s/{VERSION}" % APP_NAME]
    elif IS_WINDOWS:
        command += [
            "--msvc=latest",
            "--windows-icon-from-ico=" + str(ROOT / "resources" / "static" / "app.ico"),
            "--windows-console-mode=" + ("force" if console else "attach"),
            "--output-filename=%s.exe" % APP_NAME,
        ]
    else: 
        command += [
            "--include-qt-plugins=sensible,qml",
            "--include-module=PySide6.QtQuickControls2",
            "--include-module=PySide6.QtQuick",
            "--include-module=PySide6.QtQml",
            "--macos-create-app-bundle",
            "--macos-app-name=" + APP_NAME,
            "--macos-app-version=" + numeric,
            "--macos-app-icon=" + str(ROOT / "resources" / "static" / "app.icns"),
            "--output-filename=" + APP_NAME,
        ]
    return command


def ensure_macos_qml_controls(app_bundle: Path, source_qml: Path) -> None:
    target_qml = app_bundle / "Contents" / "MacOS" / "PySide6" / "qml"
    if not source_qml.is_dir():
        raise SystemExit("[build] каталог QML PySide6 не найден: %s" % source_qml)
    required = (
        "QtQuick/Controls",
        "QtQuick/Controls/Basic",
        "QtQuick/Controls/Fusion",
    )
    for relative in required:
        src = source_qml / relative
        if not (src / "qmldir").is_file():
            raise SystemExit("[build] отсутствует QML-модуль: %s" % src)
        dst = target_qml / relative
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src, dst, symlinks=True, ignore=shutil.ignore_patterns(
                "objects-RelWithDebInfo", "objects-Debug", "*.o", "*.cpp.o"))
            log("QML-модуль добавлен: %s" % relative)
    controls = target_qml / "QtQuick" / "Controls"
    plugins = list(controls.glob("*qtquickcontrols2plugin*"))
    if not plugins:
        raise SystemExit("[build] отсутствует qtquickcontrols2plugin в %s" % controls)
    log("QtQuick.Controls plugin: %s" % plugins[0])


def build_output_paths(mode: str) -> Dict[str, Path]:
    if IS_WINDOWS:
        dist = ROOT / "dist-win"
    elif IS_MACOS:
        dist = ROOT / "dist-mac"
    else:
        dist = ROOT / "dist-linux"
    stem = MAIN_FILE.stem
    if IS_MACOS:
        produced = BUILD_DIR / (stem + ".app")
        target = dist / (APP_NAME + ".app")
    elif mode == "onefile":
        produced = BUILD_DIR / (APP_NAME + (".exe" if IS_WINDOWS else ".bin"))
        target = dist / produced.name
    else:
        produced = BUILD_DIR / (stem + ".dist")
        target = dist / APP_NAME
    return {"dist": dist, "produced": produced, "target": target}


def publish(produced: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_dir():
        shutil.rmtree(target)
    elif target.exists():
        target.unlink()
    if produced.is_dir():
        shutil.copytree(produced, target, symlinks=True)
    else:
        shutil.copy2(produced, target)
    log("результат: %s" % target)


def report_size(target: Path) -> None:
    if target.is_file():
        log("размер: %.1f МБ" % (target.stat().st_size / 1e6))
        return
    files = [p for p in target.rglob("*") if p.is_file()]
    total = sum(p.stat().st_size for p in files)
    log("размер каталога: %.1f МБ, файлов: %d" % (total / 1e6, len(files)))
    for path in sorted(files, key=lambda p: p.stat().st_size, reverse=True)[:15]:
        log("   %7.1f МБ  %s" % (path.stat().st_size / 1e6, path.relative_to(target).as_posix()))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Сборка клиента Gorizont-VS-VDI"
    )
    default_mode = "standalone" if (IS_WINDOWS or IS_MACOS) else "onefile"
    parser.add_argument("--mode", choices=("onefile", "standalone"), default=default_mode,
                        help="onefile — один исполняемый файл (Linux по умолчанию), standalone — каталог "
                             "(Windows/macOS по умолчанию)")
    parser.add_argument("--jobs", type=int, default=os.cpu_count() or 2, help="параллельных компиляций C")
    parser.add_argument("--no-prune", action="store_true",
                        help="не удалять лишние QML-модули и плагины из PySide6 в venv (сборка будет большой)")
    parser.add_argument("--force-prune", action="store_true",
                        help="чистить PySide6, даже если интерпретатор не из venv")
    parser.add_argument("--no-resources", action="store_true", help="не пересобирать .qm и rc_resource.py")
    parser.add_argument("--console", action="store_true", help="Windows: собрать с окном консоли (отладка)")
    parser.add_argument("--onefile-cache", action="store_true",
                        help="Linux onefile: распаковывать в ~/.cache один раз на версию, а не в /tmp при каждом запуске")
    parser.add_argument("--system-openssl", action="store_true",
                        help="Linux: не включать libssl/libcrypto в сборку, использовать системные (как для ALT p10)")
    parser.add_argument("--keep-build", action="store_true", help="не удалять каталог deployment/*.build")
    parser.add_argument("--dry-run", action="store_true", help="только показать, что будет сделано")
    args = parser.parse_args(argv)

    if sys.version_info < (3, 9):
        raise SystemExit("[build] нужен Python 3.9+")
    if not MAIN_FILE.is_file():
        raise SystemExit("[build] не найден %s" % MAIN_FILE)
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    if not in_venv and not args.no_prune and not args.force_prune:
        raise SystemExit("[build] %s — не venv. Чистка PySide6 изменила бы системную установку; запускайте сборку "
                         "интерпретатором venv проекта либо укажите --no-prune (большая сборка) или --force-prune"
                         % sys.executable)

    paths = pyside_paths()
    log("Python %s, PySide6 %s (%s)" % (platform.python_version(), paths["version"], paths["package"]))
    try:
        import nuitka  # noqa: F401
    except ImportError:
        raise SystemExit("[build] Nuitka не установлена в %s (pip install \"Nuitka>=2.7\" ordered-set zstandard%s)"
                         % (sys.executable, "" if IS_WINDOWS else " patchelf"))

    version = read_version()
    if not args.no_resources and not args.dry_run:
        rebuild_resources()
    if IS_MACOS and not args.no_prune:
        log("macOS: очистка PySide6 отключена для сохранения QML-плагинов")
    elif not args.no_prune:
        prune_pyside(paths, dry_run=args.dry_run)

    command = nuitka_command(args.mode, args.jobs, args.console, args.onefile_cache, version,
                             system_openssl=args.system_openssl)
    outputs = build_output_paths(args.mode)
    if args.dry_run:
        log("команда Nuitka:\n  " + "\n  ".join(command))
        log("результат будет в %s" % outputs["target"])
        return 0

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    if outputs["produced"].exists():
        if outputs["produced"].is_dir():
            shutil.rmtree(outputs["produced"])
        else:
            outputs["produced"].unlink()
    env = dict(os.environ)
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    run(command, cwd=str(ROOT), env=env)

    if not outputs["produced"].exists():
        raise SystemExit("[build] Nuitka не создала %s" % outputs["produced"])
    if IS_MACOS:
        ensure_macos_qml_controls(outputs["produced"], paths["qml"])
    publish(outputs["produced"], outputs["target"])
    report_size(outputs["target"])
    if not args.keep_build:
        for build_dir in BUILD_DIR.glob("*.build"):
            shutil.rmtree(build_dir, ignore_errors=True)
        for onefile_dir in BUILD_DIR.glob("*.onefile-build"):
            shutil.rmtree(onefile_dir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

