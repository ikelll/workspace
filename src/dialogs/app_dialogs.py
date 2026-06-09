from __future__ import annotations

import threading
from typing import Callable, TypeVar

from PySide6.QtCore import QCoreApplication, QObject, Qt, Signal # type: ignore
from PySide6.QtWidgets import QApplication, QDialog, QWidget # type: ignore

from src.dialogs.confirm_dialog import ConfirmDialog
from src.ssl_trust import CertificateInfo, format_certificate_message

T = TypeVar("T")


class _GuiThreadRunner(QObject):
    run_requested = Signal(object)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.run_requested.connect(self._execute, Qt.ConnectionType.QueuedConnection)

    def _execute(self, payload: object) -> None:
        fnc, event, result = payload
        try:
            result["value"] = fnc()
        except Exception as exc:
            result["error"] = exc
        finally:
            event.set()


_runner: _GuiThreadRunner | None = None


def _get_runner() -> _GuiThreadRunner | None:
    global _runner
    app = QApplication.instance()
    if app is None:
        return None
    if _runner is None:
        _runner = _GuiThreadRunner(app)
    return _runner


def _run_on_gui_thread(fnc: Callable[[], T]) -> T:
    app = QApplication.instance()
    if app is None or threading.current_thread() is threading.main_thread():
        return fnc()

    runner = _get_runner()
    if runner is None:
        return fnc()

    event = threading.Event()
    result: dict[str, object] = {}
    runner.run_requested.emit((fnc, event, result))
    event.wait()

    error = result.get("error")
    if error is not None:
        raise error
    return result.get("value")


def _confirm_impl(
    parent: QWidget | None,
    title: str,
    text: str,
    confirm_text: str = "OK",
    cancel_text: str = "Cancel",
    kind: str = "primary",
) -> bool:
    dlg = ConfirmDialog(
        title=title,
        text=text,
        confirm_text=confirm_text,
        cancel_text=cancel_text,
        kind=kind,
        parent=parent,
    )
    return dlg.exec() == QDialog.DialogCode.Accepted


def confirm(
    parent: QWidget | None,
    title: str,
    text: str,
    confirm_text: str = "OK",
    cancel_text: str = "Cancel",
    kind: str = "primary",
) -> bool:
    return _run_on_gui_thread(
        lambda: _confirm_impl(
            parent=parent,
            title=title,
            text=text,
            confirm_text=confirm_text,
            cancel_text=cancel_text,
            kind=kind,
        )
    )


def alert(
    parent: QWidget | None,
    title: str,
    text: str,
    *,
    button_text: str = "OK",
    kind: str = "danger",
) -> None:
    _run_on_gui_thread(
        lambda: _confirm_impl(
            parent=parent,
            title=title,
            text=text,
            confirm_text=button_text,
            cancel_text="",
            kind=kind,
        )
    )


def confirm_certificate(parent: QWidget | None, cert: CertificateInfo, errors: list[str] | None = None) -> bool:
    return confirm(
        parent=parent,
        title=QCoreApplication.translate("AppDialogs", "Trust certificate?"),
        text=format_certificate_message(cert, errors),
        confirm_text=QCoreApplication.translate("AppDialogs", "Trust"),
        cancel_text=QCoreApplication.translate("AppDialogs", "Cancel"),
        kind="warning",
    )
