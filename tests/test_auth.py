from __future__ import annotations

import sys
from unittest import mock

from src.api import auth
from src.api import endpoints as ep


def _service():
    client = mock.MagicMock()
    return auth.AuthService(client), client


def _collect(signal) -> list:
    box: list = []
    signal.connect(lambda *a: box.append(a if len(a) != 1 else a[0]))
    return box


class TestAuthBasics:
    def test_initial_properties(self) -> None:
        svc, _ = _service()
        assert svc.token == ""
        assert svc.scrambler == ""
        assert svc.username == ""
        assert svc.is_authenticated is False

    def test_fetch_authenticators(self) -> None:
        svc, client = _service()
        svc.fetch_authenticators("https://srv/")
        client.set_base_url.assert_called_once_with("https://srv/")
        client.clear_token.assert_called_once()
        client.get.assert_called_once()
        assert client.get.call_args.args[0] == ep.AUTH_AUTHS

    def test_login_posts_body(self) -> None:
        svc, client = _service()
        svc.login("a1", "  user ", "pass")
        assert svc.username == "user"
        client.post.assert_called_once()
        assert client.post.call_args.args[0] == ep.AUTH_LOGIN
        body = client.post.call_args.kwargs["body"]
        assert body["auth_id"] == "a1"
        assert body["password"] == "pass"
        assert body["platform"] in {"Linux", "Windows", "MacOsX"}

    def test_verify_mfa_posts(self) -> None:
        svc, client = _service()
        svc.verify_mfa("mfatok", "123456", remember_device=True)
        assert client.post.call_args.args[0] == ep.AUTH_MFA
        assert client.post.call_args.kwargs["body"]["code"] == "123456"

    def test_clear_session(self) -> None:
        svc, client = _service()
        svc._token = "x"
        svc.clear_session()
        assert svc.token == ""
        client.clear_token.assert_called()


class TestAuthenticatorsParsing:
    def test_on_auths_ok_emits_list(self) -> None:
        svc, _ = _service()
        ready = _collect(svc.authenticators_ready)
        svc._on_auths_ok({"result": [{"auth_id": "a1", "auth": "Local", "type": "internal"}]})
        assert ready and ready[0][0]["id"] == "a1"
        assert ready[0][0]["name"] == "Local"

    def test_on_auths_ok_list_form_and_label_fallback(self) -> None:
        svc, _ = _service()
        ready = _collect(svc.authenticators_ready)
        svc._on_auths_ok([{"authId": "a2", "auth_label": "AD"}])
        assert ready[0][0]["id"] == "a2"
        assert ready[0][0]["name"] == "AD"

    def test_on_auths_ok_empty_emits_error(self) -> None:
        svc, _ = _service()
        errs = _collect(svc.auth_error)
        svc._on_auths_ok({"result": []})
        assert errs

    def test_on_auths_fail(self) -> None:
        svc, _ = _service()
        errs = _collect(svc.auth_error)
        svc._on_auths_fail("boom", 500)
        assert errs == ["boom"]


class TestLoginResponses:
    def test_login_ok_sets_token_and_emits(self) -> None:
        svc, client = _service()
        ok = _collect(svc.login_success)
        svc._on_login_ok({"result": "ok", "token": "TK", "scrambler": "SC", "username": "bob", "last_login": "today"})
        assert svc.token == "TK"
        assert svc.scrambler == "SC"
        client.set_token.assert_called_once_with("TK")
        client.set_scrambler.assert_called_once_with("SC")
        assert ok and ok[0][0] == "TK"

    def test_login_ok_without_token_errors(self) -> None:
        svc, _ = _service()
        errs = _collect(svc.login_error)
        svc._on_login_ok({"result": "ok"})
        assert errs

    def test_login_non_dict_errors(self) -> None:
        svc, _ = _service()
        errs = _collect(svc.login_error)
        svc._on_login_ok("nope")
        assert errs

    def test_login_rejected_translates_error(self) -> None:
        svc, _ = _service()
        errs = _collect(svc.login_error)
        svc._on_login_ok({"result": "error", "error": "Invalid credentials"})
        assert errs == ["Invalid username or password"]

    def test_mfa_required_emits_payload(self) -> None:
        svc, _ = _service()
        box = _collect(svc.mfa_required)
        svc._on_login_ok({"result": "mfa_required", "mfa_token": "M1", "methods": ["totp"]})
        assert box and box[0]["mfa_token"] == "M1"

    def test_mfa_required_without_token_errors(self) -> None:
        svc, _ = _service()
        errs = _collect(svc.login_error)
        svc._on_login_ok({"result": "mfa_required"})
        assert errs

    def test_normalize_mfa_payload_nested_and_aliases(self) -> None:
        svc, _ = _service()
        out = svc._normalize_mfa_payload({"mfa": {"mfaToken": "X"}})
        assert out["mfa_token"] == "X"

    def test_on_login_fail_auth_codes(self) -> None:
        svc, _ = _service()
        errs = _collect(svc.login_error)
        svc._on_login_fail("whatever", 401)
        assert errs == ["Invalid username or password"]

    def test_on_login_fail_other_code(self) -> None:
        svc, _ = _service()
        errs = _collect(svc.login_error)
        svc._on_login_fail("session expired", 500)
        assert errs and "sign in again" in errs[0]


class TestLogout:
    def test_logout_without_token(self) -> None:
        svc, client = _service()
        out = _collect(svc.logged_out)
        svc.logout()
        assert out
        client.get.assert_not_called()

    def test_logout_with_token_calls_api(self) -> None:
        svc, client = _service()
        svc._token = "tok"
        svc.logout()
        assert client.get.call_args.args[0] == ep.AUTH_LOGOUT


class TestNegotiate:
    def test_login_negotiate_backend_unavailable(self) -> None:
        svc, _ = _service()
        errs = _collect(svc.login_error)
        with mock.patch.dict(sys.modules, {"src.auth.negotiate": None}):
            svc.login_negotiate("a1")
        assert errs

    def test_login_negotiate_empty_host(self) -> None:
        svc, client = _service()
        client.base_url = "https://"
        errs = _collect(svc.login_error)
        fake_mod = mock.MagicMock()
        with mock.patch.dict(sys.modules, {"src.auth.negotiate": fake_mod}):
            svc.login_negotiate("a1")
        assert errs

    def test_login_negotiate_runs_step(self) -> None:
        svc, client = _service()
        client.base_url = "https://broker.example.com"
        fake_mod = mock.MagicMock()
        neg_instance = fake_mod.NegotiateClient.return_value
        neg_instance.step.return_value = ("OUTTOKEN", False)
        with mock.patch.dict(sys.modules, {"src.auth.negotiate": fake_mod}):
            svc.login_negotiate("a1", spn="HTTP/broker.example.com")
        assert client.post.call_args.args[0] == ep.AUTH_LOGIN_NEGOTIATE
        assert client.post.call_args.kwargs["body"]["out_token_b64"] == "OUTTOKEN"

    def test_run_negotiate_step_no_client(self) -> None:
        svc, _ = _service()
        errs = _collect(svc.login_error)
        svc._run_negotiate_step("a1", "", "", "Linux")
        assert errs

    def test_on_login_negotiate_continue_recurses(self) -> None:
        svc, client = _service()
        svc._negotiate_client = mock.MagicMock()
        svc._negotiate_client.step.return_value = ("NEXT", False)
        svc._on_login_negotiate_ok({"result": "continue", "context_id": "c1", "in_token_b64": "IN"}, "a1", "Linux")
        assert client.post.called

    def test_on_login_negotiate_non_dict(self) -> None:
        svc, _ = _service()
        errs = _collect(svc.login_error)
        svc._on_login_negotiate_ok("nope", "a1", "Linux")
        assert errs

    def test_on_login_negotiate_finalizes(self) -> None:
        svc, client = _service()
        svc._negotiate_client = mock.MagicMock()
        svc._negotiate_client.initiator_name = "ivan@REALM"
        ok = _collect(svc.login_success)
        svc._on_login_negotiate_ok(
            {"result": "ok", "token": "TK"}, "a1", "Linux"
        )
        assert ok and svc.token == "TK"
        assert svc.username == "ivan"
