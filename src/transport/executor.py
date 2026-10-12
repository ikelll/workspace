from __future__ import annotations

import base64
import bz2
import contextlib
import functools
import http.client
import json
import logging
import re
import ssl
import subprocess
import sys  # noqa: F401
import threading
import time
import types as pytypes  # noqa: F401
import typing
import urllib.error
import urllib.parse
import urllib.request
from urllib.parse import urlparse

from PySide6.QtCore import QCoreApplication, QObject, QThread, Qt, Signal, Slot  # type: ignore

from src.api.error_messages import translate_server_message
from src.dialogs.app_dialogs import confirm_certificate
from src.ssl_trust import (
    SslTrustStore,
    connect_with_trust,
    create_pinned_context,
    create_verified_context,
    fetch_certificate_info,
    verify_pinned_peer,
)
from src.transport import consts as tc  # noqa: F401
from src.transport.client_options import UnsafeTransportParams, apply_client_transport_options
from src.transport import tools as tools_mod
from src.transport import tunnel as tunnel_mod  # noqa: F401
from src.utils import consts

log = logging.getLogger(__name__)
_trust_store = SslTrustStore()


class TransportError(Exception):
    """Generic transport error."""


class RetryableTransportError(TransportError):
    """Server asked us to retry."""

    def __init__(self, message: str, raw_error: str = ""):
        super().__init__(message)
        self.raw_error = raw_error


class SignatureError(TransportError):
    """Script signature verification failed."""


FETCH_TIMEOUT_S = 60


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, *args: typing.Any, fingerprint: str = "", **kwargs: typing.Any) -> None:
        super().__init__(*args, **kwargs)
        self._fingerprint = fingerprint

    def connect(self) -> None:
        super().connect()
        try:
            verify_pinned_peer(typing.cast(ssl.SSLSocket, self.sock), self._fingerprint)
        except Exception:
            self.close()
            raise


class _PinnedHTTPSHandler(urllib.request.HTTPSHandler):
    def __init__(self, fingerprint: str) -> None:
        super().__init__(context=create_pinned_context())
        self._fingerprint = fingerprint

    def https_open(self, req: urllib.request.Request) -> typing.Any:
        return self.do_open(
            functools.partial(_PinnedHTTPSConnection, fingerprint=self._fingerprint),
            req,
            context=self._context,  # type: ignore[attr-defined]
        )


def _open_json(opener: urllib.request.OpenerDirector, req: urllib.request.Request) -> typing.Any:
    try:
        with opener.open(req, timeout=FETCH_TIMEOUT_S) as resp:
            raw = resp.read()
    except urllib.error.HTTPError:
        raise
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, ssl.SSLCertVerificationError):
            raise exc.reason from exc
        raise
    return json.loads(raw.decode("utf-8"))


def _fetch_json(
    url: str,
    headers: dict[str, str],
    check_certificate: bool = True,
) -> typing.Any:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    port = int(parsed.port or 443)

    if not check_certificate:
        raise TransportError("TLS certificate validation is required")
    if parsed.scheme != "https":
        return _open_json(urllib.request.build_opener(), urllib.request.Request(url, headers=headers))

    def _verified() -> typing.Any:
        ctx = create_verified_context(cafile=tools_mod.get_cacerts_file())
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
        return _open_json(opener, urllib.request.Request(url, headers=headers))

    def _pinned(fingerprint: str) -> typing.Any:
        opener = urllib.request.build_opener(_PinnedHTTPSHandler(fingerprint))
        return _open_json(opener, urllib.request.Request(url, headers=headers))

    return connect_with_trust(
        host,
        port,
        _trust_store,
        attempt_verified=_verified,
        attempt_pinned=_pinned,
        fetch_cert=lambda: fetch_certificate_info(host, port, server_hostname=host),
        prompt=lambda cert, errors, changed: confirm_certificate(None, cert, errors, changed=changed),
    )


def _unpack_transport_result(
    res: typing.Any,
) -> typing.Tuple[bytes, str, dict, dict]:
    if isinstance(res, dict):
        nested_error = res.get("error") or res.get("detail") or res.get("message")
        if nested_error:
            raise TransportError(translate_server_message(nested_error))

        if not all(key in res for key in ("script", "signature", "params")):
            log.warning("Transport endpoint returned unsupported object: %r", res)
            raise TransportError(
                QCoreApplication.translate(
                    "TransportExecutor",
                    "The server did not return a transport script.",
                )
            )

        script = bz2.decompress(base64.b64decode(res["script"]))
        signature = res["signature"]
        params = json.loads(bz2.decompress(base64.b64decode(res["params"])))
        log_data = res.get("log", {})
        return script, signature, params, log_data

    if isinstance(res, str):
        text = res.strip()
        if text.startswith("TransportScript("):
            script_b64 = re.search(r"script='([^']+)'", text)
            sig_b64 = re.search(r"signature_b64='([^']+)'", text)
            params_match = re.search(r"parameters=({.+})\)$", text, re.DOTALL)
            import ast

            if not script_b64 or not sig_b64:
                raise TransportError(
                    QCoreApplication.translate(
                        "TransportExecutor",
                        "Cannot parse transport script response.",
                    )
                )

            script = bz2.decompress(base64.b64decode(script_b64.group(1)))
            signature = sig_b64.group(1)
            params = ast.literal_eval(params_match.group(1)) if params_match else {}
            return script, signature, params, {}

        if text:
            log.warning("Transport endpoint returned error text instead of a script: %r", text[:300])
            raise TransportError(translate_server_message(text))

        log.warning("Transport endpoint returned an empty string instead of a script")
        raise TransportError(
            QCoreApplication.translate(
                "TransportExecutor",
                "The server did not return a transport script.",
            )
        )

    log.warning("Transport endpoint returned unsupported response type: %s", type(res))
    raise TransportError(
        QCoreApplication.translate(
            "TransportExecutor",
            "The server did not return a transport script.",
        )
    )


class _SubprocessWaitPatcher:

    _lock = threading.Lock()
    _depth = 0
    _original: typing.Optional[typing.Callable[..., subprocess.Popen]] = None
    _seen_pids: set[int] = set()

    @classmethod
    def _wrapper(cls, *args: typing.Any, **kwargs: typing.Any) -> subprocess.Popen:
        original = cls._original or subprocess.Popen
        proc = typing.cast(subprocess.Popen, original(*args, **kwargs))  # type: ignore[misc]
        try:
            pid = int(getattr(proc, "pid", 0) or 0)
            with cls._lock:
                fresh = bool(pid) and pid not in cls._seen_pids
                if fresh:
                    cls._seen_pids.add(pid)
            if fresh:
                tools_mod.add_task_to_wait(proc, wait_subprocesses=True)
        except Exception:  # noqa: BLE001
            pass
        return proc

    def __enter__(self) -> _SubprocessWaitPatcher:
        cls = type(self)
        with cls._lock:
            if cls._depth == 0:
                cls._original = subprocess.Popen
                subprocess.Popen = cls._wrapper  # type: ignore[assignment,misc]
            cls._depth += 1
        return self

    def __exit__(self, *args: typing.Any) -> None:
        cls = type(self)
        with cls._lock:
            if cls._depth <= 0:
                return
            cls._depth -= 1
            if cls._depth == 0 and cls._original is not None:
                subprocess.Popen = cls._original  # type: ignore[misc]
                cls._original = None


def _post_launch_cleanup() -> None:
    time.sleep(3)
    with contextlib.suppress(Exception):
        tools_mod.unlink_files(early_stage=True)
    with contextlib.suppress(Exception):
        tools_mod.wait_for_tasks()
    with contextlib.suppress(Exception):
        tools_mod.unlink_files(early_stage=False)
    with contextlib.suppress(Exception):
        tools_mod.execute_before_exit()


class _FetchAndRunWorker(QObject):
    finished = Signal()
    error = Signal(int, str, bool)
    script_started = Signal(int)

    def __init__(
        self,
        base_url: str,
        token: str,
        scrambler: str,
        service_id: str,
        transport_id: str,
        transport_type: str = "",
        client_settings: dict[str, typing.Any] | None = None,
        parent_widget: typing.Any = None,
    ) -> None:
        super().__init__()
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._scrambler = scrambler
        self._service_id = service_id
        self.launch_id = 0
        self._transport_id = transport_id
        self._transport_type = transport_type
        self._client_settings = client_settings or {}
        self._parent_widget = parent_widget

    @staticmethod
    def _interrupted() -> bool:
        thread = QThread.currentThread()
        return bool(thread is not None and thread.isInterruptionRequested())

    @Slot()
    def run(self) -> None:
        try:
            hostname = tools_mod.gethostname()
            url = (
                f"{self._base_url}/gorizontvs/rest/connection"
                f"/{self._service_id}/{self._transport_id}"
                f"/{self._scrambler}/{hostname}"
            )
            headers = {
                "X-Auth-Token": self._token,
                "Scrambler": self._scrambler,
                "User-Agent": consts.USER_AGENT,
            }

            log.info(
                "Fetching transport script: service=%s transport=%s",
                self._service_id,
                self._transport_id,
            )
            try:
                data = _fetch_json(url, headers)
            except urllib.error.HTTPError as exc:
                if exc.code in (401, 403):
                    self.error.emit(self.launch_id, translate_server_message("session expired"), False)
                    return
                raise

            if self._interrupted():
                log.info("Launch cancelled before script execution")
                return

            if isinstance(data, dict) and "error" in data:
                error_msg = data["error"]
                retryable = data.get("is_retrayable", data.get("retryable", "0")) == "1"
                self.error.emit(self.launch_id, translate_server_message(error_msg), retryable)
                return

            result = data.get("result", data) if isinstance(data, dict) else data
            script_bytes, signature, params, _ = _unpack_transport_result(result)

            if not tools_mod.verify_signature(script_bytes, signature.encode()):
                log.error("Transport script signature INVALID")
                self.error.emit(self.launch_id, 
                    QCoreApplication.translate(
                        "TransportExecutor",
                        "Transport script signature verification failed.\n"
                        "Contact your administrator.",
                    ),
                    False,
                )
                return

            try:
                params = apply_client_transport_options(
                    params,
                    self._transport_type,
                    self._client_settings,
                )
            except UnsafeTransportParams as exc:
                log.error("Rejected transport parameters: %s", exc)
                self.error.emit(self.launch_id, 
                    QCoreApplication.translate(
                        "TransportExecutor",
                        "The server requested to start an unexpected program. "
                        "The connection was blocked. Contact your administrator.",
                    ),
                    False,
                )
                return

            if self._interrupted():
                log.info("Launch cancelled before script execution")
                return

            log.info(
                "Signature verified, executing transport script (%d bytes)",
                len(script_bytes),
            )

            script_text = script_bytes.decode("utf-8")

            self.script_started.emit(self.launch_id)

            ns: dict[str, typing.Any] = {
                "__builtins__": __builtins__,
                "parent": self._parent_widget,
                "sp": params,
            }

            with _SubprocessWaitPatcher():
                exec(script_text, ns)  # noqa: S102

            threading.Thread(target=_post_launch_cleanup, daemon=True).start()

        except RetryableTransportError as e:
            self.error.emit(self.launch_id, str(e), True)
        except Exception as e:
            log.exception("Transport script execution failed")
            self.error.emit(self.launch_id, str(e), False)
        finally:
            self.finished.emit()


class TransportExecutor(QObject):
    launch_started = Signal()
    launch_ok = Signal()
    launch_error = Signal(str)
    launch_retry = Signal(str)
    launch_finished = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker: _FetchAndRunWorker | None = None
        self._orphans: list[tuple[QThread, _FetchAndRunWorker]] = []
        self._launch_seq = 0
        self._current_launch = 0

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.isRunning()

    def launch(
        self,
        base_url: str,
        token: str,
        scrambler: str,
        service_id: str,
        transport_id: str,
        transport_type: str = "",
        client_settings: dict[str, typing.Any] | None = None,
        parent_widget: typing.Any = None,
    ) -> None:

        if self.is_running:
            log.warning("Transport already running, ignoring duplicate launch")
            return

        self.launch_started.emit()

        thread = QThread(self)
        worker = _FetchAndRunWorker(
            base_url=base_url,
            token=token,
            scrambler=scrambler,
            service_id=service_id,
            transport_id=transport_id,
            transport_type=transport_type,
            client_settings=client_settings,
            parent_widget=parent_widget,
        )
        self._launch_seq += 1
        worker.launch_id = self._launch_seq
        self._current_launch = self._launch_seq
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.script_started.connect(self._on_script_started)
        worker.error.connect(self._on_error)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(self._on_thread_done, Qt.ConnectionType.QueuedConnection)

        self._thread = thread
        self._worker = worker
        thread.start()

    def stop(self, wait_ms: int = 200) -> None:
        thread, worker = self._thread, self._worker
        if thread is None:
            return
        self._thread = None
        self._worker = None
        self._current_launch = 0
        with contextlib.suppress(Exception):
            thread.requestInterruption()
        with contextlib.suppress(Exception):
            thread.quit()
        finished = False
        with contextlib.suppress(Exception):
            finished = bool(thread.wait(max(0, wait_ms)))
        if not finished and worker is not None:
            log.info("Transport worker is still finishing; detached")
            self._orphans.append((thread, worker))
        elif not finished:
            self._orphans.append((thread, typing.cast(_FetchAndRunWorker, None)))
        else:
            thread.deleteLater()
        self.launch_finished.emit()

    def wait_for_orphans(self, timeout_ms: int = 2000) -> None:
        for thread, _worker in list(self._orphans):
            with contextlib.suppress(Exception):
                thread.wait(timeout_ms)

    def _is_current(self, launch_id: int) -> bool:
        return launch_id != 0 and launch_id == self._current_launch

    @Slot(int)
    def _on_script_started(self, launch_id: int) -> None:
        if not self._is_current(launch_id):
            return
        self.launch_ok.emit()

    @Slot(int, str, bool)
    def _on_error(self, launch_id: int, msg: str, retryable: bool) -> None:
        if not self._is_current(launch_id):
            log.info("Ignoring error from a cancelled launch: %s", msg)
            return
        if retryable:
            self.launch_retry.emit(msg)
        else:
            self.launch_error.emit(msg)

    @Slot()
    def _on_thread_done(self) -> None:
        thread = self.sender()
        orphan = next((item for item in self._orphans if item[0] is thread), None)
        if orphan is not None:
            self._orphans.remove(orphan)
            typing.cast(QThread, thread).deleteLater()
            return
        if thread is not self._thread:
            return
        self._thread = None
        self._worker = None
        self._current_launch = 0
        typing.cast(QThread, thread).deleteLater()
        self.launch_finished.emit()
