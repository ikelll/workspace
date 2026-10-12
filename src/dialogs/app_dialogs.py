from __future__ import annotations

import logging
import threading
import typing
from typing import Callable, TypeVar

from PySide6.QtCore import QCoreApplication, QObject, Qt, Signal  # type: ignore

from src.ssl_trust import CertificateInfo, format_certificate_message

log = logging.getLogger(__name__)

T = TypeVar("T")
PromptBackend = Callable[[str, str, str, str, str], bool]


class _GuiThreadRunner(QObject):
    run_requested = Signal(object)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.run_requested.connect(self._execute, Qt.ConnectionType.QueuedConnection)

    def _execute(self, payload: object) -> None:
        fnc, event, result = payload
        try:
            result["value"] = fnc()
        except Exception as exc:  # noqa: BLE001
            result["error"] = exc
        finally:
            event.set()


_runner: _GuiThreadRunner | None = None
_backend: PromptBackend | None = None
_closing = threading.Event()


def set_prompt_backend(backend: PromptBackend | None) -> None:
    global _backend
    _backend = backend
    if backend is not None:
        _closing.clear()


def close_prompts() -> None:
    _closing.set()


def _get_runner() -> _GuiThreadRunner | None:
    global _runner
    app = QCoreApplication.instance()
    if app is None:
        return None
    if _runner is None:
        runner = _GuiThreadRunner()
        if runner.thread() is not app.thread():
            runner.moveToThread(app.thread())
        _runner = runner
    return _runner


def _run_on_gui_thread(fnc: Callable[[], T]) -> T:
    app = QCoreApplication.instance()
    if app is None or threading.current_thread() is threading.main_thread():
        return fnc()

    runner = _get_runner()
    if runner is None:
        return fnc()

    event = threading.Event()
    result: dict[str, object] = {}
    runner.run_requested.emit((fnc, event, result))
    while not event.wait(0.5):
        if _closing.is_set():
            return typing.cast(T, False)

    error = result.get("error")
    if error is not None:
        raise error  # type: ignore[misc]
    return result.get("value")  # type: ignore[return-value]


def _ask(kind: str, title: str, text: str, confirm_text: str, cancel_text: str) -> bool:
    if _closing.is_set():
        return False
    if _backend is None:
        log.warning("Prompt requested without UI backend: %s — %s", title, text)
        return False
    return bool(_backend(kind, title, text, confirm_text, cancel_text))


def confirm(
    parent: object | None,
    title: str,
    text: str,
    confirm_text: str = "OK",
    cancel_text: str = "Cancel",
    kind: str = "primary",
) -> bool:
    del parent
    return _run_on_gui_thread(lambda: _ask(kind, title, text, confirm_text, cancel_text))


def alert(
    parent: object | None,
    title: str,
    text: str,
    *,
    button_text: str = "OK",
    kind: str = "danger",
) -> None:
    del parent
    _run_on_gui_thread(lambda: _ask(kind, title, text, button_text, ""))


def confirm_certificate(
    parent: object | None,
    cert: CertificateInfo,
    errors: list[str] | None = None,
    *,
    changed: bool = False,
) -> bool:
    return confirm(
        parent=parent,
        title=QCoreApplication.translate("AppDialogs", "Trust certificate?"),
        text=format_certificate_message(cert, errors, changed=changed),
        confirm_text=QCoreApplication.translate("AppDialogs", "Trust"),
        cancel_text=QCoreApplication.translate("AppDialogs", "Cancel"),
        kind="warning",
    )
