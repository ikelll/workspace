from __future__ import annotations

import json
from unittest import mock

from PySide6.QtCore import QUrl  # type: ignore
from PySide6.QtNetwork import QNetworkReply, QNetworkRequest  # type: ignore

from src.api import endpoints as ep
from src.api import error_messages, services
from src.api.client import ApiClient

class TestEndpoints:
    def test_url_builders(self) -> None:
        assert ep.service_transport("svc", "tr") == "/gorizontvs/rest/connection/svc/tr"
        assert ep.service_image("img1") == f"{ep.SERVICE_IMAGE_WEB}/img1"

    def test_static_constants(self) -> None:
        assert ep.AUTH_LOGIN.endswith("/auth/login")
        assert ep.HEADER_AUTH_TOKEN == "X-Auth-Token"

class TestErrorMessages:
    def test_empty_message(self) -> None:
        assert error_messages.translate_server_message("") == "Unexpected server response"
        assert error_messages.translate_server_message(None) == "Unexpected server response"

    def test_invalid_credentials(self) -> None:
        assert (
            error_messages.translate_server_message("Invalid credentials")
            == "Invalid username or password"
        )

    def test_maintenance_variants(self) -> None:
        for raw in (
            "The requested service is in maintenance mode",
            "service is in maintenance mode",
        ):
            assert (
                error_messages.translate_server_message(raw)
                == "This service is in maintenance mode"
            )

    def test_not_accessible_and_preparation(self) -> None:
        assert error_messages.translate_server_message("not_accesible") == "Unavailable"
        assert "being prepared" in error_messages.translate_server_message(
            "service in preparation"
        )

    def test_max_services_and_password_backed(self) -> None:
        assert "maximum number" in error_messages.translate_server_message(
            "max services reached"
        )
        assert "requires a password" in error_messages.translate_server_message(
            "this transport requires a password-backed session"
        )

    def test_session_expired(self) -> None:
        assert "sign in again" in error_messages.translate_server_message("session expired")

    def test_unknown_message_passthrough(self) -> None:
        assert error_messages.translate_server_message("Some weird error") == "Some weird error"

    def test_normalize_collapses_whitespace(self) -> None:
        assert error_messages._normalize("  Foo   BAR ") == "foo bar"

class TestServiceInfoProperties:
    def test_is_available(self) -> None:
        assert services.ServiceInfo().is_available is True
        assert services.ServiceInfo(maintenance=True).is_available is False
        assert services.ServiceInfo(not_accessible=True).is_available is False

    def test_status_text_catalog_and_fallbacks(self) -> None:
        assert services.ServiceInfo(status_code="on").status_text == "Powered on"
        assert services.ServiceInfo(status_code="off").status_text == "Powered off"
        assert services.ServiceInfo(status_code="weird", status_label="Custom").status_text == "Custom"
        assert services.ServiceInfo(maintenance=True).status_text == "This service is in maintenance mode"
        assert services.ServiceInfo(not_accessible=True).status_text == "Unavailable"
        assert services.ServiceInfo(in_use=True).status_text == "In use"
        assert services.ServiceInfo().status_text == "Available"

    def test_is_desktop(self) -> None:
        assert services.ServiceInfo(is_application=False).is_desktop is True
        assert services.ServiceInfo(is_application=True).is_desktop is False
        assert services.ServiceInfo(name="My VDI desktop").is_desktop is True
        assert services.ServiceInfo(name="Calculator app").is_desktop is False

    def test_default_transport(self) -> None:
        assert services.ServiceInfo().default_transport is None
        svc = services.ServiceInfo(
            transports=[
                services.TransportInfo(id="a", priority=5),
                services.TransportInfo(id="b", priority=1),
            ]
        )
        assert svc.default_transport.id == "b"


class TestServicesParsing:
    def test_coerce_optional_bool(self) -> None:
        c = services.ServicesAPI._coerce_optional_bool
        assert c(None) is None
        assert c(True) is True
        assert c(1) is True
        assert c(0) is False
        assert c("yes") is True
        assert c("off") is False
        assert c("maybe") is None

    def test_clean_optional_text(self) -> None:
        c = services.ServicesAPI._clean_optional_text
        assert c(None) is None
        assert c("  ") is None
        assert c("  hi ") == "hi"

    def test_parse_service_non_dict(self) -> None:
        assert services.ServicesAPI._parse_service("nope") is None  # type: ignore[arg-type]

    def test_parse_service_full(self) -> None:
        raw = {
            "id": "s1",
            "name": "svc",
            "visual_name": "My Service",
            "group": {"id": "g1", "name": "Group", "priority": 2, "imageUuid": "img"},
            "transports": [
                {"id": "t1", "name": "RDP", "priority": 1, "type": "rdp", "is_application": False},
                {"id": "", "name": "skip-me"},
            ],
            "maintenance": True,
            "not_accesible": False,
        }
        svc = services.ServicesAPI._parse_service(raw)
        assert svc is not None
        assert svc.id == "s1"
        assert svc.group.name == "Group"
        assert len(svc.transports) == 1
        assert svc.transports[0].id == "t1"
        assert svc.maintenance is True
        assert svc.is_application is False


class TestServicesAPISignals:
    def _api(self):
        client = mock.MagicMock()
        return services.ServicesAPI(client), client

    def test_fetch_services_calls_client(self) -> None:
        api, client = self._api()
        api.fetch_services()
        client.get.assert_called_once()
        assert client.get.call_args.args[0] == ep.SERVICES_OVERVIEW

    def test_on_services_ok_emits_ready(self) -> None:
        api, _ = self._api()
        got: list = []
        api.services_ready.connect(got.append)
        api._on_services_ok({"result": {"services": [{"id": "s1", "transports": []}]}})
        assert len(got) == 1
        assert got[0][0].id == "s1"

    def test_on_services_ok_bad_data_emits_error(self) -> None:
        api, _ = self._api()
        errors: list = []
        api.services_error.connect(errors.append)
        with mock.patch.object(services.ServicesAPI, "_parse_service", side_effect=RuntimeError("x")):
            api._on_services_ok({"result": {"services": [{"id": "s1"}]}})
        assert errors

    def test_on_services_fail_emits_error(self) -> None:
        api, _ = self._api()
        errors: list = []
        api.services_error.connect(errors.append)
        api._on_services_fail("Invalid credentials", 401)
        assert errors == ["Invalid username or password"]

    def test_connect_service_flow(self) -> None:
        api, client = self._api()
        api.connect_service("s1", "t1")
        client.get.assert_called_once()

        ready: list = []
        api.connect_ready.connect(lambda sid, link: ready.append((sid, link)))
        api._on_connect_ok("s1", {"result": "rdp://link"})
        assert ready == [("s1", "rdp://link")]

        errs: list = []
        api.connect_error.connect(errs.append)
        api._on_connect_ok("s1", {"error": "session expired"})
        assert errs and "sign in again" in errs[0]

    def test_service_action_done(self) -> None:
        api, client = self._api()
        api.service_action("s1", "reset")
        client.get.assert_called_once()
        done: list = []
        api.action_done.connect(lambda sid, act: done.append((sid, act)))
        api._on_action_ok("s1", "reset")
        assert done == [("s1", "reset")]

def _make_reply(*, body: bytes = b"", status: int | None = 200,
                error=QNetworkReply.NetworkError.NoError, content_type: str = "application/json"):
    reply = mock.MagicMock()
    reply.error.return_value = error
    reply.attribute.return_value = status
    reply.errorString.return_value = "some error"
    reply.readAll.return_value.data.return_value = body
    reply.url.return_value = QUrl("https://example.com/x")
    reply.rawHeader.return_value = content_type
    return reply


class TestApiClientConfig:
    def test_setters_and_props(self) -> None:
        c = ApiClient()
        c.set_base_url("https://srv/")
        assert c.base_url == "https://srv"
        assert c.has_token is False
        c.set_token("tok")
        assert c.has_token is True
        c.clear_token()
        assert c.has_token is False
        c.set_scrambler("scr")
        c.set_ignore_ssl_errors(True)
        c.set_timeout(5000)
        c.set_ssl_dialog_parent(None)

    def test_build_url_with_params(self) -> None:
        c = ApiClient()
        c.set_base_url("https://srv")
        url = c._build_url("/path", {"a": "1", "b": "2"})
        s = url.toString()
        assert s.startswith("https://srv/path?")
        assert "a=1" in s and "b=2" in s

    def test_build_request_sets_headers(self) -> None:
        c = ApiClient()
        c.set_base_url("https://srv")
        c.set_token("mytoken")
        c.set_scrambler("myscr")
        req = c._build_request(c._build_url("/p"))
        assert bytes(req.rawHeader("User-Agent")).decode().startswith("GorizontVS/")
        assert bytes(req.rawHeader("X-Auth-Token")).decode() == "mytoken"
        assert bytes(req.rawHeader("Scrambler")).decode() == "myscr"


class TestApiClientReplyHandling:
    def test_handle_reply_json(self) -> None:
        c = ApiClient()
        ok: list = []
        c._handle_reply(_make_reply(body=b'{"k":1}'), ok.append, mock.MagicMock())
        assert ok == [{"k": 1}]

    def test_handle_reply_empty_body(self) -> None:
        c = ApiClient()
        ok: list = []
        c._handle_reply(_make_reply(body=b""), ok.append, mock.MagicMock())
        assert ok == [{}]

    def test_handle_reply_non_json(self) -> None:
        c = ApiClient()
        ok: list = []
        c._handle_reply(_make_reply(body=b"plain text"), ok.append, mock.MagicMock())
        assert ok == ["plain text"]

    def test_handle_reply_http_error_status(self) -> None:
        c = ApiClient()
        err: list = []
        reply = _make_reply(body=json.dumps({"error": "Invalid credentials"}).encode(), status=400)
        c._handle_reply(reply, mock.MagicMock(), lambda m, s: err.append((m, s)))
        assert err and err[0][1] == 400
        assert err[0][0] == "Invalid username or password"

    def test_handle_reply_network_error(self) -> None:
        c = ApiClient()
        err: list = []
        reply = _make_reply(error=QNetworkReply.NetworkError.HostNotFoundError, status=0)
        c._handle_reply(reply, mock.MagicMock(), lambda m, s: err.append((m, s)))
        assert err and "Server not found" in err[0][0]

    def test_handle_binary_reply(self) -> None:
        c = ApiClient()
        ok: list = []
        reply = _make_reply(body=b"\x89PNG", content_type="image/png")
        c._handle_binary_reply(reply, lambda raw, ct: ok.append((raw, ct)), mock.MagicMock())
        assert ok == [(b"\x89PNG", "image/png")]


class TestApiClientRequests:
    def _client(self):
        c = ApiClient()
        c.set_base_url("https://srv")
        c._nam = mock.MagicMock()
        reply = mock.MagicMock()
        for m in ("get", "post", "put", "deleteResource"):
            getattr(c._nam, m).return_value = reply
        return c, reply

    def test_get_connects_reply(self) -> None:
        c, reply = self._client()
        c.get("/p", mock.MagicMock(), mock.MagicMock(), params={"a": "1"})
        c._nam.get.assert_called_once()
        reply.finished.connect.assert_called_once()
        reply.sslErrors.connect.assert_called_once()
        reply.finished.connect.call_args.args[0]()
        reply.deleteLater.assert_called_once()

    def test_get_bytes(self) -> None:
        c, reply = self._client()
        c.get_bytes("/img", mock.MagicMock(), mock.MagicMock())
        c._nam.get.assert_called_once()
        reply.finished.connect.call_args.args[0]()
        reply.deleteLater.assert_called_once()

    def test_post_sets_content_type(self) -> None:
        c, reply = self._client()
        c.post("/p", {"k": "v"}, mock.MagicMock(), mock.MagicMock())
        c._nam.post.assert_called_once()

    def test_put(self) -> None:
        c, reply = self._client()
        c.put("/p", {"k": "v"}, mock.MagicMock(), mock.MagicMock())
        c._nam.put.assert_called_once()

    def test_delete(self) -> None:
        c, reply = self._client()
        c.delete("/p", mock.MagicMock(), mock.MagicMock())
        c._nam.deleteResource.assert_called_once()


class TestApiClientSslErrors:
    def test_ignored_when_ignore_flag_set(self) -> None:
        c = ApiClient()
        c.set_ignore_ssl_errors(True)
        reply = mock.MagicMock()
        reply.url.return_value = QUrl("https://h:443/x")
        c._handle_ssl_errors(reply, [])
        reply.ignoreSslErrors.assert_called_once()

    def test_prompts_and_remembers_on_accept(self) -> None:
        c = ApiClient()
        c._ssl_trust_store = mock.MagicMock()
        c._ssl_trust_store.is_trusted.return_value = False
        reply = mock.MagicMock()
        reply.url.return_value = QUrl("https://h:443/x")
        err = mock.MagicMock()
        cert = mock.MagicMock()
        cert.isNull.return_value = False
        cert.toDer.return_value = b"DER"
        err.certificate.return_value = cert
        err.errorString.return_value = "self signed"
        with mock.patch("src.api.client.describe_der_certificate") as desc, mock.patch(
            "src.api.client.confirm_certificate", return_value=True
        ):
            desc.return_value = mock.MagicMock()
            c._handle_ssl_errors(reply, [err])
        c._ssl_trust_store.remember.assert_called_once()
        reply.ignoreSslErrors.assert_called_once()
