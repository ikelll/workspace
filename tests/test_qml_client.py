from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")

import pytest  # noqa: E402

pytest.importorskip("PySide6.QtQuick")

from PySide6.QtCore import QElapsedTimer, QMetaObject, QObject, QSettings, QTimer, Qt  # noqa: E402  # type: ignore
from PySide6.QtTest import QTest  # noqa: E402  # type: ignore
from PySide6.QtWidgets import QApplication  # noqa: E402  # type: ignore

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import resources.rc_resource  # noqa: E402, F401
from fake_broker import FakeBroker  # noqa: E402
from src.qmlui import app as qml_app  # noqa: E402
from src.transport import tools as tools_mod  # noqa: E402


@pytest.fixture(scope="module")
def app():
    application = QApplication.instance()
    if application is None or not isinstance(application, QApplication):
        application = QApplication([])
    qml_app.load_fonts(application)
    return application


@pytest.fixture
def broker():
    instance = FakeBroker().start()
    yield instance
    instance.stop()


class Harness:
    def __init__(self, app, tmp_path, monkeypatch):
        self.app = app
        monkeypatch.setattr(tools_mod, "verify_signature", lambda script, sig: True)
        self.settings = QSettings(str(tmp_path / "client.ini"), QSettings.Format.IniFormat)
        self.warnings: list[str] = []
        original = qml_app.QQmlApplicationEngine
        harness = self

        class Engine(original):
            def __init__(self, *args):
                super().__init__(*args)
                self.warnings.connect(lambda messages: harness.warnings.extend(m.toString() for m in messages))

        monkeypatch.setattr(qml_app, "QQmlApplicationEngine", Engine)
        self.engine, self.client = qml_app.create_engine(app, self.settings)
        self.window = self.engine.rootObjects()[0]
        self.window.resize(1360, 860)

    def close(self):
        import shiboken6
        self.window.close()
        self.client.shutdown()
        shiboken6.delete(self.engine)

    def wait(self, predicate, timeout=8000):
        timer = QElapsedTimer()
        timer.start()
        while not predicate() and timer.elapsed() < timeout:
            self.app.processEvents()
            QTest.qWait(10)
        assert predicate(), "timeout"

    def items(self):
        result = []

        def walk(item):
            for child in item.childItems():
                result.append(child)
                walk(child)

        walk(self.window.contentItem())
        return result

    def by_name(self, name):
        found = self.window.findChild(QObject, name)
        if found is None:
            found = next((o for o in self.items() if o.objectName() == name), None)
        assert found is not None, name
        return found

    def click(self, name):
        QMetaObject.invokeMethod(self.by_name(name), "clicked")

    def login(self, broker, username="alex.smirnov", password="secret"):
        self.by_name("serverField").setProperty("text", broker.url)
        self.click("serverContinue")
        self.wait(lambda: self.client.loginPage == "credentials")
        self.by_name("userField").setProperty("text", username)
        self.by_name("passwordField").setProperty("text", password)
        self.click("loginSubmit")

    def connect_button(self, service_id):
        from PySide6.QtQml import QJSValue  # type: ignore
        for item in self.items():
            if item.metaObject().className().startswith("ConnectButton"):
                service = item.property("service")
                if isinstance(service, QJSValue):
                    service = service.toVariant()
                if isinstance(service, dict) and service.get("id") == service_id and item.property("visible"):
                    return item
        raise AssertionError(service_id)

    def answer_prompt_later(self, accepted, delay=300):
        def _answer():
            dialog = self.by_name("promptDialog")
            assert dialog.property("visible")
            QMetaObject.invokeMethod(dialog, "accept" if accepted else "reject")
        QTimer.singleShot(delay, _answer)


def test_login_workspace_favorites_and_logout(app, broker, tmp_path, monkeypatch):
    h = Harness(app, tmp_path, monkeypatch)
    try:
        assert h.client.screen == "login" and h.client.loginPage == "server"
        h.login(broker)
        h.wait(lambda: h.client.screen == "main")
        QTest.qWait(100)
        services = h.client.services
        assert len(services) == 6 and {s["kind"] for s in services} == {"app", "desktop"}
        statuses = {s["id"]: s["statusKind"] for s in services}
        assert statuses["svc-win"] == "success" and statuses["svc-ubuntu"] == "neutral" and statuses["svc-ps"] == "danger"
        assert h.client.displayName == "Alex Smirnov" and h.client.initials == "AS"
        assert len(h.client.profiles) == 1 and h.client.profiles[0]["username"] == "alex.smirnov"
        assert h.client.imageAvailable("img-win", h.client.imageVersion)
        assert h.client.toggleFavorite("svc-excel")
        h.settings.sync()
        assert "svc-excel" in [str(v) for v in h.settings.value("workspace/favorite_service_ids", [])]
        assert next(s for s in h.client.services if s["id"] == "svc-excel")["favorite"]
        screen = next(o for o in h.items() if o.property("primaryPages") is not None and o.property("page") is not None)
        for page in ("apps", "desktops", "favorites", "settings", "transport", "profile", "about", "home"):
            screen.setProperty("page", page)
            QTest.qWait(50)
            h.app.processEvents()
        h.client.logout()
        h.wait(lambda: h.client.screen == "login")
        assert h.client.loginPage == "password" and broker.logged_out == 1
        assert not h.client.authenticated and h.client.services == []
        assert not h.warnings, h.warnings
    finally:
        h.close()


def test_wrong_password_shows_error_on_credentials_page(app, broker, tmp_path, monkeypatch):
    h = Harness(app, tmp_path, monkeypatch)
    try:
        h.login(broker, password="wrong")
        h.wait(lambda: h.client.screen == "login" and h.client.loginError != "")
        assert h.client.loginPage == "credentials" and not h.client.loginBusy
        assert "парол" in h.client.loginError.lower() or "password" in h.client.loginError.lower()
    finally:
        h.close()


def test_mfa_setup_and_verify(app, broker, tmp_path, monkeypatch):
    h = Harness(app, tmp_path, monkeypatch)
    try:
        h.login(broker, username="mfa")
        h.wait(lambda: h.client.loginPage == "mfaSetup")
        assert h.client.mfa["qrImage"].startswith("data:image/png;base64,")
        assert "Google Authenticator" in h.client.mfa["message"] and "authenticator" in h.client.mfa["message"].lower()
        QTest.qWait(200)
        qr = next(o for o in h.items() if o.objectName() == "mfaQrImage")
        assert qr.property("progress") == 1.0 and qr.property("paintedWidth") > 0
        h.client.mfaContinue()
        assert h.client.loginPage == "mfaVerify"
        h.client.verifyMfa("000000", True)
        h.wait(lambda: h.client.loginPage == "mfaVerify" and h.client.loginError != "")
        h.client.verifyMfa("123456", True)
        h.wait(lambda: h.client.screen == "main")
        assert h.client.username == "mfa"
    finally:
        h.close()


def test_connect_flow_custom_message_script_and_retry(app, broker, tmp_path, monkeypatch):
    flag = tmp_path / "transport-flag"
    monkeypatch.setenv("FAKE_TRANSPORT_FLAG", str(flag))
    h = Harness(app, tmp_path, monkeypatch)
    try:
        h.login(broker)
        h.wait(lambda: h.client.screen == "main")
        h.answer_prompt_later(False)
        h.client.connectService("svc-ubuntu", "")
        QTest.qWait(200)
        assert not flag.exists() and h.client.screen == "main"
        h.client.connectService("svc-win", "t-spice")
        h.wait(lambda: flag.exists())
        h.wait(lambda: h.client.screen == "main")
        win_button = h.connect_button("svc-win")
        assert h.client.connecting and h.client.connectingServiceId == "svc-win"
        assert win_button.property("busy") is True and win_button.property("ready") is False
        assert h.connect_button("svc-excel").property("ready") is False
        requests_before = len(broker.requests)
        h.wait(lambda: not h.client.connecting)
        h.app.processEvents()
        assert win_button.property("ready") is True and win_button.property("busy") is False
        assert h.connect_button("svc-excel").property("ready") is True
        assert h.client.connectingServiceId == ""
        assert not any(p == "/gorizontvs/rest/connection" for _m, p in broker.requests[requests_before:])
        assert any(p.startswith("/gorizontvs/rest/connection/svc-win/t-spice/") for _m, p in broker.requests)
        broker.transport_mode = "retry"
        h.answer_prompt_later(False, delay=600)
        h.client.connectService("svc-excel", "")
        h.wait(lambda: h.client.screen == "main" and not h.client.connecting)
        QTest.qWait(800)
        assert h.client.screen == "main"
        h.client.serviceAction("svc-win", "reset")
        h.wait(lambda: ("svc-win", "reset") in broker.actions)
        assert not h.warnings, h.warnings
    finally:
        h.close()


def test_prompts_work_from_worker_threads(app, broker, tmp_path, monkeypatch):
    import threading
    from src.dialogs import app_dialogs
    h = Harness(app, tmp_path, monkeypatch)
    try:
        result = {}

        def worker():
            result["value"] = app_dialogs.confirm(None, "Доверять сертификату?", "CN=broker", "Доверять", "Отмена", kind="warning")

        h.answer_prompt_later(True, delay=400)
        thread = threading.Thread(target=worker)
        thread.start()
        h.wait(lambda: not thread.is_alive(), timeout=5000)
        assert result["value"] is True
    finally:
        h.close()


def test_language_changes_visible_text_and_catalog_without_refresh(app, broker, tmp_path, monkeypatch):
    h = Harness(app, tmp_path, monkeypatch)
    try:
        assert h.client.language == "ru_RU"
        assert h.by_name("serverContinue").property("text") == "Продолжить"
        h.client.setLanguage("en_US")
        h.app.processEvents()
        assert h.by_name("serverContinue").property("text") == "Continue"
        h.login(broker)
        h.wait(lambda: h.client.screen == "main")
        request_count = len(broker.requests)
        h.client.setLanguage("ru_RU")
        h.app.processEvents()
        assert h.by_name("pageSettings").property("title") == "Настройки"
        assert next(s for s in h.client.services if s["id"] == "svc-win")["statusText"] == "Доступен"
        h.client.setLanguage("en_US")
        h.app.processEvents()
        assert h.by_name("pageSettings").property("title") == "Settings"
        assert next(s for s in h.client.services if s["id"] == "svc-win")["statusText"] == "Available"
        assert h.settings.value("ui/language") == "en_US"
        assert len(broker.requests) == request_count
        h.client.setLanguage("ru_RU")
        h.app.processEvents()
        assert h.by_name("pageSettings").property("title") == "Настройки"
        assert not h.warnings, h.warnings
    finally:
        h.close()
