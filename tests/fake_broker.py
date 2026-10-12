from __future__ import annotations

import base64
import bz2
import io
import json
import struct
import threading
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOKEN = "test-token-123"
SCRAMBLER = "scr"
MFA_TOKEN = "mfa-token-1"


def _png(width: int, height: int, rgb: tuple[int, int, int]) -> bytes:
    raw = b"".join(b"\x00" + bytes(rgb) * width for _ in range(height))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


IMAGES = {
    "img-win": _png(64, 64, (37, 99, 235)),
    "img-ubuntu": _png(64, 64, (234, 88, 12)),
    "img-1c": _png(64, 64, (202, 138, 4)),
    "img-excel": _png(64, 64, (22, 163, 74)),
    "img-word": _png(64, 64, (29, 78, 216)),
}


def _transport(tid: str, name: str, ttype: str, priority: int, is_app: bool) -> dict:
    return {"id": tid, "name": name, "link": "", "priority": priority, "is_application": is_app, "type": ttype}


SERVICES = [
    {"id": "svc-win", "name": "win11", "visual_name": "Windows 11", "description": "Рабочий стол Windows 11",
     "group": {"id": "g1", "name": "Рабочие столы", "priority": 1, "imageUuid": ""}, "imageId": "img-win",
     "is_application": False, "status_code": "on", "allow_users_reset": True, "allow_users_poweroff": True,
     "show_transports": True, "custom_message_text": "", "os_type": "windows_11", "os_type_name": "Windows 11", "os_family": "windows",
     "transports": [_transport("t-gvs", "Gorizont-VS Protocol", "GVS", 1, False), _transport("t-spice", "SPICE", "SPICE", 2, False)]},
    {"id": "svc-ubuntu", "name": "ubuntu", "visual_name": "Ubuntu 22.04", "description": "Рабочий стол Linux",
     "group": {"id": "g1", "name": "Рабочие столы", "priority": 1, "imageUuid": ""}, "imageId": "img-ubuntu",
     "is_application": False, "status_code": "off", "allow_users_poweron": True, "os_type": "ubuntu", "os_type_name": "Ubuntu", "os_family": "linux",
     "custom_message_text": "Сервис обслуживается по средам с 20:00 до 22:00.",
     "transports": [_transport("t-x2go", "X2Go", "X2GO", 1, False)]},
    {"id": "svc-1c", "name": "1c", "visual_name": "1С:Предприятие", "description": "Учёт",
     "group": {"id": "g2", "name": "Бизнес", "priority": 2, "imageUuid": ""}, "imageId": "img-1c",
     "is_application": True, "status_code": "preparing",
     "transports": [_transport("t-app", "Приложение", "GVS", 1, True)]},
    {"id": "svc-excel", "name": "excel", "visual_name": "Microsoft Excel", "description": "Таблицы",
     "group": {"id": "g3", "name": "Офис", "priority": 3, "imageUuid": ""}, "imageId": "img-excel",
     "is_application": True, "status_code": "on",
     "transports": [_transport("t-app", "Приложение", "GVS", 1, True)]},
    {"id": "svc-word", "name": "word", "visual_name": "Microsoft Word", "description": "Документы",
     "group": {"id": "g3", "name": "Офис", "priority": 3, "imageUuid": ""}, "imageId": "img-word",
     "is_application": True, "status_code": "on",
     "transports": [_transport("t-app", "Приложение", "GVS", 1, True)]},
    {"id": "svc-ps", "name": "photoshop", "visual_name": "Photoshop", "description": "Графика",
     "group": {"id": "g4", "name": "Дизайн", "priority": 4, "imageUuid": "x"}, "imageId": "x",
     "is_application": True, "status_code": "unavailable", "not_accesible": True,
     "transports": [_transport("t-app", "Приложение", "GVS", 1, True)]},
]

AUTHS = [
    {"auth_id": "auth-local", "auth": "Локальная база", "type": "internal", "login_methods": ["password"], "preferred_method": "password"},
    {"auth_id": "auth-ad", "auth": "Корпоративный домен", "type": "ldap", "login_methods": ["password", "negotiate"], "preferred_method": "negotiate", "spn": "HTTP/broker"},
]

SCRIPT = ("import os, time\n"
          "open(os.environ.get('FAKE_TRANSPORT_FLAG', '/tmp/fake-transport-flag'), 'w').write('ok')\n"
          "time.sleep(float(os.environ.get('FAKE_TRANSPORT_DELAY', '0.6')))\n")


def _pack(obj) -> str:
    return base64.b64encode(bz2.compress(obj if isinstance(obj, bytes) else json.dumps(obj).encode())).decode()


class FakeBroker:
    def __init__(self) -> None:
        self.requests: list[tuple[str, str]] = []
        self.actions: list[tuple[str, str]] = []
        self.transport_mode = "ok"   # ok | error | retry
        self.logged_out = 0
        self.services = [dict(s) for s in SERVICES]
        broker = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):  # noqa: D401
                return

            def _send(self, payload, status=200, content_type="application/json"):
                body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):  # noqa: N802
                broker.requests.append(("GET", self.path))
                path = self.path.split("?", 1)[0]
                if path == "/gorizontvs/rest/auth/auths":
                    return self._send({"result": AUTHS})
                if path == "/gorizontvs/rest/auth/logout":
                    broker.logged_out += 1
                    return self._send({"result": "ok"})
                if path == "/gorizontvs/rest/connection":
                    if self.headers.get("X-Auth-Token") != TOKEN:
                        return self._send({"error": "unauthorized"}, 401)
                    return self._send({"result": {"services": broker.services}})
                if path.startswith("/gorizontvs/webapi/img/gallery/"):
                    image_id = path.rsplit("/", 1)[-1]
                    if image_id in IMAGES:
                        return self._send(IMAGES[image_id], content_type="image/png")
                    return self._send(b"not found", 404, "text/plain")
                parts = path.strip("/").split("/")
                if len(parts) == 6 and parts[:3] == ["gorizontvs", "rest", "connection"] and parts[4] == "action":
                    broker.actions.append((parts[3], parts[5]))
                    return self._send({"result": "ok"})
                if len(parts) == 7 and parts[:3] == ["gorizontvs", "rest", "connection"]:
                    if broker.transport_mode == "error":
                        return self._send({"error": "Service is in maintenance", "is_retrayable": "0"})
                    if broker.transport_mode == "retry":
                        return self._send({"error": "Service is not ready yet", "is_retrayable": "1"})
                    return self._send({"result": {"script": _pack(SCRIPT.encode()), "signature": "c2ln", "params": _pack({"as_cmd": ["gorizont-spicy", "--monitors=1"]})}})
                return self._send({"error": "not found"}, 404)

            def do_POST(self):  # noqa: N802
                broker.requests.append(("POST", self.path))
                length = int(self.headers.get("Content-Length", "0") or 0)
                body = json.loads(self.rfile.read(length) or b"{}")
                if self.path == "/gorizontvs/rest/auth/login":
                    username, password = body.get("username", ""), body.get("password", "")
                    if password != "secret":
                        return self._send({"error": "invalid credentials"}, 401)
                    if username == "mfa":
                        qr = base64.b64encode(_png(120, 120, (17, 24, 39))).decode()
                        return self._send({"result": "mfa_required", "mfa_token": MFA_TOKEN, "label": "Code from the app",
                                           "message": "Please, use your Authenticator to add your account. (i.e. Google Authenticator, Yandex, ...)",
                                           "qr_image": qr})
                    return self._send({"result": "ok", "token": TOKEN, "scrambler": SCRAMBLER, "username": username,
                                       "last_login": "2026-10-06T18:42:00+00:00"})
                if self.path == "/gorizontvs/rest/auth/mfa":
                    if body.get("mfa_token") == MFA_TOKEN and body.get("code") == "123456":
                        return self._send({"result": "ok", "token": TOKEN, "scrambler": SCRAMBLER, "username": "mfa"})
                    return self._send({"result": "error", "error": "Invalid code"})
                return self._send({"error": "not found"}, 404)

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def url(self) -> str:
        return "http://127.0.0.1:%d" % self._server.server_address[1]

    def start(self) -> "FakeBroker":
        self._thread.start()
        return self

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()
