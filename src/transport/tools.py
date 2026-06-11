from __future__ import annotations

import base64
import contextlib
import hashlib
import logging
import os
import os.path
import platform
import random
import socket
import stat
import string
import sys
import tempfile
import time
import typing

from cryptography.hazmat.backends import default_backend  # type: ignore
from cryptography.hazmat.primitives import hashes, serialization  # type: ignore
from cryptography.hazmat.primitives.asymmetric import padding  # type: ignore

from src.transport.consts import PUBLIC_KEY
from src.utils.types import AwaitableTask, RemovableFile

log = logging.getLogger(__name__)

try:
    import psutil  # type: ignore

    def process_iter(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        return psutil.process_iter(*args, **kwargs)

except ImportError:

    def process_iter(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:  # type: ignore[misc]
        return []


_unlink_files: typing.List[RemovableFile] = []
_awaitable_tasks: typing.List[AwaitableTask] = []
_execute_before_exit: typing.List[typing.Callable[[], None]] = []

sys_fs_enc = sys.getfilesystemencoding() or "mbcs"


def save_temp_file(content: str, filename: typing.Optional[str] = None) -> str:
    if filename is None:
        filename = (
            "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(16))
            + ".gorizontvs"
        )
    filepath = os.path.join(tempfile.gettempdir(), filename)
    with open(filepath, "w") as f:
        f.write(content)
    log.info("Saved temp file: %s", filepath)
    return filepath


def read_temp_file(filename: str) -> typing.Optional[str]:
    filepath = os.path.join(tempfile.gettempdir(), filename)
    try:
        with open(filepath, "r") as f:
            return f.read()
    except Exception:
        return None


def test_server(host: str, port: typing.Union[str, int], timeout: int = 4) -> bool:
    try:
        sock = socket.create_connection((host, int(port)), timeout)
        sock.close()
    except Exception:
        return False
    return True


def find_application(
    application_name: str, extra_path: typing.Optional[str] = None
) -> typing.Optional[str]:
    search_path = os.environ.get("PATH", "").split(os.pathsep)
    if extra_path:
        search_path.append(extra_path)
    for path in search_path:
        file_name = os.path.join(path, application_name)
        if os.path.isfile(file_name) and (os.stat(file_name).st_mode & stat.S_IXUSR) != 0:
            return file_name
    return None


def gethostname() -> str:
    hostname = socket.gethostname()
    log.info("Hostname: %s", hostname)
    return hostname


def register_for_delayed_deletion(filename: str, early_stage: bool = False) -> None:
    log.debug("Queued for deletion (%s): %s", "early" if early_stage else "late", filename)
    _unlink_files.append(RemovableFile(filename, early_stage))


def unlink_files(early_stage: bool = False) -> None:
    stage = "early" if early_stage else "late"
    log.debug("Unlinking files (%s stage)", stage)
    files_to_unlink = [f for f in _unlink_files if f.early_stage == early_stage]
    if files_to_unlink:
        time.sleep(1 + 2 * (1 + int(early_stage)))
        for f in files_to_unlink:
            try:
                os.unlink(f.path)
            except Exception as e:
                log.debug("Could not delete %s: %s", f.path, e)
    _unlink_files[:] = [f for f in _unlink_files if f not in files_to_unlink]


def add_task_to_wait(task: typing.Any, wait_subprocesses: bool = False) -> None:
    log.debug("Added task to wait: %s (subprocesses=%s)", task, wait_subprocesses)
    _awaitable_tasks.append(AwaitableTask(task, wait_subprocesses))


def wait_for_tasks() -> None:
    log.debug("Waiting for %d task(s)", len(_awaitable_tasks))
    for awaitable in _awaitable_tasks:
        try:
            if hasattr(awaitable.task, "join"):
                awaitable.task.join()
            elif hasattr(awaitable.task, "wait"):
                awaitable.task.wait()

            if awaitable.wait_subprocesses and hasattr(awaitable.task, "pid"):
                subprocesses = list(
                    filter(
                        lambda x: x.ppid() == awaitable.task.pid,
                        process_iter(attrs=("ppid",)),
                    )
                )
                for sp in subprocesses:
                    sp.wait()
        except Exception as e:
            log.error("Error waiting for task: %s", e)
    _awaitable_tasks.clear()


def terminate_tasks() -> None:
    log.debug("Terminating %d task(s)", len(_awaitable_tasks))
    for awaitable in list(_awaitable_tasks):
        task = awaitable.task
        try:
            if hasattr(task, "terminate"):
                task.terminate()
            elif hasattr(task, "kill"):
                task.kill()
            elif hasattr(task, "close"):
                task.close()
        except Exception as e:
            log.debug("Could not terminate task %s: %s", task, e)

        if awaitable.wait_subprocesses and hasattr(task, "pid"):
            try:
                for sp in filter(lambda x: x.ppid() == task.pid, process_iter(attrs=("ppid",))):
                    with contextlib.suppress(Exception):
                        sp.terminate()
            except Exception as e:
                log.debug("Could not terminate child processes for %s: %s", task, e)

    _awaitable_tasks.clear()


def register_execute_before_exit(fnc: typing.Callable[[], None]) -> None:
    log.debug("Registered before-exit callback: %s", fnc)
    _execute_before_exit.append(fnc)


def execute_before_exit() -> None:
    for fnc in _execute_before_exit:
        try:
            fnc()
        except Exception as e:
            log.error("before-exit callback error: %s", e)
    _execute_before_exit.clear()


def verify_signature(script: bytes, signature: bytes) -> bool:
    public_key = serialization.load_pem_public_key(
        data=PUBLIC_KEY,
        backend=default_backend(),
    )

    try:
        signature_raw = base64.b64decode(signature.strip())
    except Exception as e:
        log.exception("Could not base64-decode transport signature: %r", e)
        signature_raw = signature

    log.warning("=== VERIFY SIGNATURE DEBUG START ===")
    log.warning("python executable: %s", sys.executable)
    log.warning("python version: %s", sys.version.replace("\n", " "))
    log.warning("platform: %s", platform.platform())

    try:
        import cryptography  # type: ignore

        log.warning("cryptography version: %s", getattr(cryptography, "__version__", "unknown"))
    except Exception as e:
        log.warning("cryptography import failed: %r", e)

    log.warning("PUBLIC_KEY len: %s", len(PUBLIC_KEY))
    log.warning("PUBLIC_KEY sha256: %s", hashlib.sha256(PUBLIC_KEY).hexdigest())
    log.warning("PUBLIC_KEY head: %r", PUBLIC_KEY[:80])
    log.warning("PUBLIC_KEY tail: %r", PUBLIC_KEY[-80:])

    log.warning("script bytes len: %s", len(script))
    log.warning("script sha256: %s", hashlib.sha256(script).hexdigest())
    log.warning("script head: %r", script[:300])
    log.warning("script tail: %r", script[-300:])
    log.warning("script count LF: %s", script.count(b"\n"))
    log.warning("script count CRLF: %s", script.count(b"\r\n"))
    log.warning("script count CR: %s", script.count(b"\r"))

    log.warning("signature input len: %s", len(signature))
    log.warning("signature input sha256: %s", hashlib.sha256(signature).hexdigest())
    log.warning("signature input head: %r", signature[:120])
    log.warning("signature input tail: %r", signature[-120:])

    log.warning("signature raw len: %s", len(signature_raw))
    log.warning("signature raw sha256: %s", hashlib.sha256(signature_raw).hexdigest())
    log.warning("signature raw head: %r", signature_raw[:40])
    log.warning("signature raw tail: %r", signature_raw[-40:])

    try:
        public_key.verify(  # type: ignore[union-attr]
            signature_raw,
            script,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
    except Exception as e:
        log.exception("Transport script signature verify failed: %r", e)
        log.warning("=== VERIFY SIGNATURE DEBUG END ===")
        return False

    log.warning("Transport script signature VALID")
    log.warning("=== VERIFY SIGNATURE DEBUG END ===")
    return True


def get_cacerts_file() -> typing.Optional[str]:
    if "CERTIFICATE_BUNDLE_PATH" in os.environ:
        return os.environ["CERTIFICATE_BUNDLE_PATH"]
    try:
        import certifi  # type: ignore

        if os.path.exists(certifi.where()):
            return certifi.where()
    except Exception:
        pass
    if "linux" in sys.platform:
        for path in (
            "/etc/pki/tls/certs/ca-bundle.crt",
            "/etc/ssl/certs/ca-certificates.crt",
            "/etc/ssl/ca-bundle.pem",
        ):
            if os.path.exists(path):
                return path
    return None


def is_macos() -> bool:
    return "darwin" in sys.platform


def is_linux() -> bool:
    return "linux" in sys.platform


def is_windows() -> bool:
    return "win" in sys.platform


saveTempFile = save_temp_file
readTempFile = read_temp_file
testServer = test_server
findApp = find_application
addTaskToWait = add_task_to_wait
addFileToUnlink = register_for_delayed_deletion
