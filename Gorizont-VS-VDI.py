from __future__ import annotations

import atexit
import logging
import sys

from src.infrastructure.logging_setup import setup_logging

setup_logging()

import resources.rc_resource as rc_resource  # noqa: E402, F401
from src.qmlui import app as qml_app  # noqa: E402
from src.transport import tools as tools_mod  # noqa: E402
from src.transport import tunnel as tunnel_mod  # noqa: E402
from src.utils.version import APP_VERSION  # noqa: E402

log = logging.getLogger(__name__)

_cleanup_done = False


def _cleanup_on_exit() -> None:
    global _cleanup_done
    if _cleanup_done:
        return
    _cleanup_done = True
    for fn in (
        tunnel_mod.stop_all,
        lambda: tools_mod.unlink_files(True, delay=False),
        lambda: tools_mod.unlink_files(False, delay=False),
        tools_mod.execute_before_exit,
    ):
        try:
            fn()
        except Exception:  # noqa: BLE001
            pass


atexit.register(_cleanup_on_exit)

if __name__ == "__main__":
    log.info("Starting Gorizont-VS-VDI Client v%s", APP_VERSION)
    code = qml_app.run(sys.argv)
    _cleanup_on_exit()
    sys.exit(code)
