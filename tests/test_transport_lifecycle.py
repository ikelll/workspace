from __future__ import annotations
import base64
import bz2
import json
import threading
import time
import pytest
from PySide6.QtCore import QElapsedTimer, QThread
from src.transport import executor as mod


def response(script="pass"):
    return {
        "script": base64.b64encode(bz2.compress(script.encode())).decode(),
        "signature": "test",
        "params": base64.b64encode(bz2.compress(json.dumps({}).encode())).decode(),
    }


def wait(app, predicate):
    timer = QElapsedTimer()
    timer.start()
    while not predicate() and timer.elapsed() < 5000:
        app.processEvents()
        time.sleep(0.005)
    assert predicate()


@pytest.mark.parametrize("data,valid", [({"error": "denied"}, True), (response(), False), (response(), True)])
def test_worker_emits_finished_once(monkeypatch, data, valid):
    monkeypatch.setattr(mod, "_fetch_json", lambda *a: data)
    monkeypatch.setattr(mod.tools_mod, "verify_signature", lambda *a: valid)
    monkeypatch.setattr(mod, "_post_launch_cleanup", lambda: None)
    worker = mod._FetchAndRunWorker("https://example.invalid", "token", "scrambler", "s", "t")
    finished = []
    worker.finished.connect(lambda: finished.append(True))
    worker.run()
    assert finished == [True]


@pytest.mark.parametrize("script", ["pass", "raise RuntimeError('launch failed')"])
def test_completion_allows_next_launch_on_ui_thread(_qapp, monkeypatch, script):
    monkeypatch.setattr(mod, "_fetch_json", lambda *a: response(script))
    monkeypatch.setattr(mod.tools_mod, "verify_signature", lambda *a: True)
    monkeypatch.setattr(mod, "_post_launch_cleanup", lambda: None)
    transport = mod.TransportExecutor()
    observed = []
    transport.launch_finished.connect(lambda: observed.append((threading.get_ident(), transport.is_running)))
    for count in (1, 2):
        transport.launch("https://example.invalid", "token", "scrambler", "s", "t")
        wait(_qapp, lambda: len(observed) == count)
        assert observed[-1] == (threading.get_ident(), False)
        assert transport.thread() == QThread.currentThread()
    _qapp.processEvents()
    assert len(observed) == 2
