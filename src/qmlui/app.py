from __future__ import annotations

import getpass
import logging
import os
import signal
import sys
from pathlib import Path

import PySide6  # type: ignore
from PySide6.QtCore import QCoreApplication, QSettings, QTimer, QUrl, Qt, qVersion  # type: ignore
from PySide6.QtGui import QFont, QFontDatabase, QIcon  # type: ignore
from PySide6.QtQml import QQmlApplicationEngine  # type: ignore
from PySide6.QtQuickControls2 import QQuickStyle  # type: ignore
from PySide6.QtNetwork import QLocalServer, QLocalSocket  # type: ignore
from PySide6.QtWidgets import QApplication  # type: ignore

from src.api.client import ApiClient
from src.qmlui.controller import ClientController
from src.qmlui.images import PROVIDER_ID, ServiceImageProvider, ServiceImageStore
from src.qmlui.prompts import QmlPrompter
from src.utils.version import APP_VERSION

log = logging.getLogger(__name__)

QML_DIR = Path(__file__).resolve().parent / "qml"


def load_fonts(app: QApplication) -> None:
    for name in ("Regular", "Medium", "SemiBold", "Bold", "Light", "Black"):
        QFontDatabase.addApplicationFont(f":/fonts/fonts/Montserrat-{name}.ttf")
    if "Montserrat" in QFontDatabase.families():
        font = QFont("Montserrat")
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        app.setFont(font)


def main_qml_url() -> QUrl:
    if (QML_DIR / "Main.qml").is_file():
        return QUrl.fromLocalFile(str(QML_DIR / "Main.qml"))
    return QUrl("qrc:/qml/Main.qml")


def create_engine(app: QApplication, settings: QSettings | None = None) -> tuple[QQmlApplicationEngine, ClientController]:
    settings = settings or QSettings("Gorizont-VS", "VDIClient")
    api = ApiClient(parent=app)
    api.set_timeout(15_000)
    images = ServiceImageStore(api, parent=app)
    prompter = QmlPrompter(parent=app)
    controller = ClientController(settings, api, images, prompter, parent=app)
    controller.applyLanguage()

    QQuickStyle.setStyle("Fusion")
    QQuickStyle.setFallbackStyle("Basic")
    engine = QQmlApplicationEngine()
    engine.addImageProvider(PROVIDER_ID, ServiceImageProvider(images))
    engine.rootContext().setContextProperty("client", controller)
    engine.rootContext().setContextProperty("prompts", prompter)
    controller.languageChanged.connect(engine.retranslate)
    engine.load(main_qml_url())
    if not engine.rootObjects():
        raise RuntimeError("QML interface failed to load")
    controller.start()
    return engine, controller


def _prepare_qt_runtime() -> None:
    compiled = "__compiled__" in globals()
    paths = [str(path) for path in QCoreApplication.libraryPaths()]
    log.info("Qt %s, PySide6 %s, Python %s, compiled=%s", qVersion(), PySide6.__version__,
             sys.version.split()[0], compiled)
    if compiled:
        dist_root = Path(__file__).resolve().parents[2]          # <dist>/src/qmlui/app.py
        plugins = dist_root / "PySide6" / "qt-plugins"
        if plugins.is_dir():
            if str(plugins) not in paths:
                QCoreApplication.addLibraryPath(str(plugins))
                paths = [str(path) for path in QCoreApplication.libraryPaths()]
            platforms = plugins / "platforms"
            found = sorted(path.name for path in platforms.iterdir()) if platforms.is_dir() else []
            log.info("Qt platform plugins in %s: %s", platforms, ", ".join(found) or "directory is empty or missing!")
        else:
            log.warning("Qt plugin directory not found: %s", plugins)
    log.info("Qt plugin search paths: %s; QML import path: %s", paths,
             os.environ.get("QML2_IMPORT_PATH") or os.environ.get("QML_IMPORT_PATH") or "")


def _choose_scene_graph_backend() -> None:
    if sys.platform != "linux" or os.environ.get("QT_QUICK_BACKEND") or os.environ.get("QSG_RHI_BACKEND"):
        return
    try:
        from PySide6.QtGui import QOpenGLContext  # type: ignore
        context = QOpenGLContext()
        usable = context.create()
    except Exception:  # noqa: BLE001
        usable = False
    if not usable:
        log.warning("OpenGL context is not available; switching Qt Quick to software rendering (QT_QUICK_BACKEND=software)")
        os.environ["QT_QUICK_BACKEND"] = "software"


URL_SCHEMES = ("gorizontvs://", "gorizontvss://", "gorizontvsa://")


def _instance_name() -> str:
    try:
        user = getpass.getuser()
    except Exception:  # noqa: BLE001
        user = "user"
    safe = "".join(ch for ch in user if ch.isalnum()) or "user"
    return f"GorizontVS-VDI-{safe}"


def _notify_running_instance(name: str) -> bool:
    sock = QLocalSocket()
    sock.connectToServer(name)
    if not sock.waitForConnected(300):
        return False
    sock.write(b"activate\n")
    sock.flush()
    sock.waitForBytesWritten(300)
    sock.disconnectFromServer()
    return True


def _start_instance_server(name: str, engine: QQmlApplicationEngine, parent: QApplication) -> QLocalServer | None:
    server = QLocalServer(parent)
    if not server.listen(name):
        # Stale socket left by a crashed instance.
        QLocalServer.removeServer(name)
        if not server.listen(name):
            log.warning("Single-instance server unavailable: %s", server.errorString())
            return None

    def _on_connection() -> None:
        conn = server.nextPendingConnection()
        if conn is not None:
            conn.disconnectFromServer()
        for root in engine.rootObjects():
            for method in ("show", "raise_", "requestActivate"):
                fn = getattr(root, method, None)
                if callable(fn):
                    try:
                        fn()
                    except Exception:  # noqa: BLE001
                        pass

    server.newConnection.connect(_on_connection)
    return server


def _log_url_arguments(argv: list[str]) -> None:
    for arg in argv[1:]:
        if arg.lower().startswith(URL_SCHEMES):
            log.info("Started from a %s link; link parameters are ignored", arg.split("://", 1)[0])


def install_signal_handlers(app: QApplication) -> QTimer:
    def _handler(*_args: object) -> None:
        log.info("Termination signal received")
        QCoreApplication.quit()

    for sig in (getattr(signal, "SIGINT", None), getattr(signal, "SIGTERM", None)):
        if sig is not None:
            try:
                signal.signal(sig, _handler)
            except Exception:  # noqa: BLE001
                pass
    timer = QTimer(app)
    timer.setInterval(250)
    timer.timeout.connect(lambda: None)
    timer.start()
    return timer


def run(argv: list[str]) -> int:
    _prepare_qt_runtime()
    app = QApplication(argv)
    app.setApplicationName("Gorizont-VS-VDI")
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("Gorizont-VS")
    _log_url_arguments(argv)
    name = _instance_name()
    single = os.environ.get("GORIZONTVS_MULTI_INSTANCE", "").strip() not in {"1", "true", "yes"}
    if single and _notify_running_instance(name):
        log.info("Another instance is already running; activated it")
        return 0
    _choose_scene_graph_backend()
    app.setWindowIcon(QIcon(":/img/static/app.png"))
    app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeMenuBar, True)
    load_fonts(app)
    install_signal_handlers(app)
    engine, controller = create_engine(app)
    if single:
        _start_instance_server(name, engine, app)
    app.aboutToQuit.connect(controller.shutdown)
    result = app.exec()
    del engine
    return result
