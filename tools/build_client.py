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
    import PySide6
    from PySide6.QtCore import QLibraryInfo

    package = Path(PySide6.__file__).resolve().parent
    try:
        location = QLibraryInfo.LibraryPath
        qml = Path(QLibraryInfo.path(location.QmlImportsPath))
        plugins = Path(QLibraryInfo.path(location.PluginsPath))
    except AttributeError: 
        qml = Path(QLibraryInfo.location(QLibraryInfo.Qml2ImportsPath))
        plugins = Path(QLibraryInfo.location(QLibraryInfo.PluginsPath))
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


def validate_source_qml(paths: Dict[str, Path]) -> None:
    if not QML_SOURCES.is_dir():
        raise SystemExit("[build] не найден каталог QML: %s" % QML_SOURCES)
    required = qml_imports_of(QML_SOURCES) | set(RUNTIME_QML_MODULES)
    required.update(("QtQml", "QtQuick", "QtQuick.Controls", "QtQuick.Layouts"))
    missing = sorted(name for name in required if name.startswith("Qt")
                     and module_dir(paths["qml"], name) is None)
    if missing:
        raise SystemExit("[build] отсутствуют QML-модули PySide6: %s. "
                         "Переустановите PySide6, PySide6-Essentials и PySide6-Addons "
                         "одной версии в окружении сборки." % ", ".join(missing))
    validate_qml_tree(paths["qml"], required)


def validate_qml_tree(qml_root: Path, required: Iterable[str]) -> None:
    for name in sorted(required):
        if not name.startswith("Qt"):
            continue
        directory = module_dir(qml_root, name)
        if directory is None:
            raise SystemExit("[build] отсутствует QML-модуль %s в %s" % (name, qml_root))
        for line in (directory / "qmldir").read_text(encoding="utf-8").splitlines():
            parts = line.split("#", 1)[0].split()
            if parts and parts[0] == "optional":
                parts = parts[1:]
            if len(parts) < 2 or parts[0] != "plugin":
                continue
            plugin = parts[1]
            plugin_dir = directory / parts[2] if len(parts) > 2 else directory
            candidates = (plugin_dir / (plugin + ".dll"),
                          plugin_dir / ("lib" + plugin + ".so"),
                          plugin_dir / (plugin + ".so"),
                          plugin_dir / ("lib" + plugin + ".dylib"),
                          plugin_dir / (plugin + ".dylib"))
            if not any(path.is_file() for path in candidates):
                raise SystemExit("[build] отсутствует QML-плагин %s (%s)" % (plugin, plugin_dir))


def validate_output(mode: str, produced: Path) -> None:
    tree = produced if produced.is_dir() else BUILD_DIR / (MAIN_FILE.stem + ".dist")
    if not tree.is_dir():
        raise SystemExit("[build] нет каталога для проверки QML: %s" % tree)
    roots = sorted({p.parent.parent for p in tree.rglob("qmldir")
                    if p.parent.name == "QtQuick"})
    required = qml_imports_of(QML_SOURCES) | set(RUNTIME_QML_MODULES)
    required.update(("QtQml", "QtQuick", "QtQuick.Controls", "QtQuick.Layouts"))
    if not roots:
        raise SystemExit("[build] Nuitka не включила QML-модули в %s" % tree)
    for root in roots:
        validate_qml_tree(root, required)
    platform_plugin = "qcocoa" if IS_MACOS else "qwindows" if IS_WINDOWS else "qxcb"
    if not any(p.is_file() and platform_plugin in p.name for p in tree.rglob("*")):
        raise SystemExit("[build] отсутствует платформенный плагин %s" % platform_plugin)
    log("проверка QML-модулей и плагинов пройдена")


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
        "--include-qt-plugins=sensible,qml",
        "--include-module=PySide6.QtCore",
        "--include-module=PySide6.QtGui",
        "--include-module=PySide6.QtQml",
        "--include-module=PySide6.QtQuick",
        "--include-module=PySide6.QtQuickControls2",
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
    if IS_LINUX:
        command += ["--include-qt-plugins=" + "platforminputcontexts"]
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
            "--macos-create-app-bundle",
            "--macos-app-name=" + APP_NAME,
            "--macos-app-version=" + numeric,
            "--macos-app-icon=" + str(ROOT / "resources" / "static" / "app.icns"),
            "--output-filename=" + APP_NAME,
        ]
    return command


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
                        help="совместимость: очистка PySide6 всегда отключена")
    parser.add_argument("--force-prune", action="store_true",
                        help="устаревший параметр; очистка PySide6 не выполняется")
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
    if IS_MACOS and args.mode != "standalone":
        raise SystemExit("[build] для macOS .app используйте --mode standalone")
    if args.system_openssl and not IS_LINUX:
        raise SystemExit("[build] --system-openssl поддерживается только на Linux")
    if args.force_prune:
        log("--force-prune устарел; установленный PySide6 не изменяется")
    paths = pyside_paths()
    log("Python %s, PySide6 %s (%s)" % (platform.python_version(), paths["version"], paths["package"]))
    try:
        import nuitka
    except ImportError:
        raise SystemExit("[build] Nuitka не установлена в %s (pip install \"Nuitka>=2.7\" ordered-set zstandard%s)"
                         % (sys.executable, "" if IS_WINDOWS else " patchelf"))

    version = read_version()
    if not args.no_resources and not args.dry_run:
        rebuild_resources()
    validate_source_qml(paths)

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
    validate_output(args.mode, outputs["produced"])
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
