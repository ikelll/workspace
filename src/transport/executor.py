from __future__ import annotations

import base64
import bz2
import contextlib
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
import urllib.parse
import urllib.request
from urllib.parse import urlparse

from PySide6.QtCore import QCoreApplication, QObject, QThread, Signal  # type: ignore

from src.dialogs.app_dialogs import confirm_certificate
from src.ssl_trust import SslTrustStore, fetch_certificate_info
from src.transport import consts as tc  # noqa: F401
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


def _build_ssl_context(check_certificate: bool = False) -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    if not check_certificate:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    cacerts = tools_mod.get_cacerts_file()
    if cacerts:
        ctx.load_verify_locations(cacerts)
    return ctx


def _fetch_json(
    url: str,
    headers: dict[str, str],
    check_certificate: bool = True,
) -> typing.Any:
    """Blocking HTTP GET that returns parsed JSON."""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    port = int(parsed.port or 443)

    if _trust_store.is_trusted(host, port):
        check_certificate = False

    req = urllib.request.Request(url, headers=headers)
    try:
        ctx = _build_ssl_context(check_certificate)
        with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
            raw = resp.read()
        return json.loads(raw.decode("utf-8"))
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", None)
        if isinstance(reason, ssl.SSLCertVerificationError):
            cert = fetch_certificate_info(host, port, server_hostname=host)
            should_trust = confirm_certificate(None, cert, [str(reason)])
            if not should_trust:
                raise
            _trust_store.remember(host, port, cert)
            ctx = _build_ssl_context(False)
            with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
                raw = resp.read()
            return json.loads(raw.decode("utf-8"))
        raise


def _unpack_transport_result(
    res: typing.Any,
) -> typing.Tuple[bytes, str, dict, dict]:
    if isinstance(res, dict):
        script = bz2.decompress(base64.b64decode(res["script"]))
        signature = res["signature"]
        params = json.loads(bz2.decompress(base64.b64decode(res["params"])))
        log_data = res.get("log", {})
        return script, signature, params, log_data

    if isinstance(res, str) and res.startswith("TransportScript("):
        script_b64 = re.search(r"script='([^']+)'", res)
        sig_b64 = re.search(r"signature_b64='([^']+)'", res)
        params_match = re.search(r"parameters=({.+})\)$", res, re.DOTALL)
        import ast

        if not script_b64 or not sig_b64:
            raise TransportError("Cannot parse TransportScript response")

        script = bz2.decompress(base64.b64decode(script_b64.group(1)))
        signature = sig_b64.group(1)
        params = ast.literal_eval(params_match.group(1)) if params_match else {}
        return script, signature, params, {}

    raise TransportError(f"Unsupported response format: {type(res)}")


class _SubprocessWaitPatcher:
    def __init__(self) -> None:
        self._orig_popen: typing.Optional[typing.Callable[..., subprocess.Popen]] = None
        self._seen_pids: set[int] = set()

    def __enter__(self) -> _SubprocessWaitPatcher:
        if self._orig_popen is not None:
            return self
        self._orig_popen = subprocess.Popen

        def _wrapper(*args: typing.Any, **kwargs: typing.Any) -> subprocess.Popen:
            proc = typing.cast(subprocess.Popen, self._orig_popen(*args, **kwargs))  # type: ignore
            try:
                pid = int(getattr(proc, "pid", 0) or 0)
                if pid and pid not in self._seen_pids:
                    self._seen_pids.add(pid)
                    tools_mod.add_task_to_wait(proc, wait_subprocesses=True)
            except Exception:
                pass
            return proc

        subprocess.Popen = _wrapper  # type: ignore[assignment]
        return self

    def __exit__(self, *args: typing.Any) -> None:
        if self._orig_popen is not None:
            subprocess.Popen = self._orig_popen  # type: ignore[assignment]
            self._orig_popen = None


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
    error = Signal(str, bool)
    script_started = Signal()

    def __init__(
        self,
        base_url: str,
        token: str,
        scrambler: str,
        service_id: str,
        transport_id: str,
        parent_widget: typing.Any = None,
    ) -> None:
        super().__init__()
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._scrambler = scrambler
        self._service_id = service_id
        self._transport_id = transport_id
        self._parent_widget = parent_widget

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

            log.info("Fetching transport script: %s", url[:120])
            data = _fetch_json(url, headers)

            if isinstance(data, dict) and "error" in data:
                error_msg = data["error"]
                retryable = data.get("is_retrayable", data.get("retryable", "0")) == "1"
                self.error.emit(str(error_msg), retryable)
                self.finished.emit()
                return

            result = data.get("result", data) if isinstance(data, dict) else data
            script_bytes, signature, params, log_data = _unpack_transport_result(result)

            if not tools_mod.verify_signature(script_bytes, signature.encode()):
                log.error("Transport script signature INVALID")
                self.error.emit(
                    QCoreApplication.translate(
                        "TransportExecutor",
                        "Transport script signature verification failed.\n"
                        "Contact your administrator.",
                    ),
                    False,
                )
                self.finished.emit()
                return

            log.info(
                "Signature verified, executing transport script (%d bytes)",
                len(script_bytes),
            )

            script_text = script_bytes.decode("utf-8")

            self.script_started.emit()

            ns: dict[str, typing.Any] = {
                "__builtins__": __builtins__,
                "parent": self._parent_widget,
                "sp": params,
            }

            with _SubprocessWaitPatcher():
                exec(script_text, ns)  # noqa: S102

            threading.Thread(target=_post_launch_cleanup, daemon=True).start()

        except RetryableTransportError as e:
            self.error.emit(str(e), True)
        except Exception as e:
            log.exception("Transport script execution failed")
            self.error.emit(str(e), False)
        finally:
            self.finished.emit()


class TransportExecutor(QObject):
    launch_started = Signal()
    launch_ok = Signal()
    launch_error = Signal(str)
    launch_retry = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker: _FetchAndRunWorker | None = None

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
        parent_widget: typing.Any = None,
    ) -> None:

        if self.is_running:
            log.warning("Transport already running, ignoring duplicate launch")
            return

        self.launch_started.emit()

        thread = QThread()
        worker = _FetchAndRunWorker(
            base_url=base_url,
            token=token,
            scrambler=scrambler,
            service_id=service_id,
            transport_id=transport_id,
            parent_widget=parent_widget,
        )
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.script_started.connect(self._on_script_started)
        worker.error.connect(self._on_error)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._on_thread_done)

        self._thread = thread
        self._worker = worker
        thread.start()

    def stop(self) -> None:
        if self._thread is None:
            return
        with contextlib.suppress(Exception):
            self._thread.requestInterruption()
        with contextlib.suppress(Exception):
            self._thread.quit()
        with contextlib.suppress(Exception):
            self._thread.wait(2000)
        self._thread = None
        self._worker = None

    def _on_script_started(self) -> None:
        self.launch_ok.emit()

    def _on_error(self, msg: str, retryable: bool) -> None:
        if retryable:
            self.launch_retry.emit(msg)
        else:
            self.launch_error.emit(msg)

    def _on_thread_done(self) -> None:
        self._thread = None
        self._worker = None
