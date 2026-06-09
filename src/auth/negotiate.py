from __future__ import annotations

import base64
import logging
import sys

log = logging.getLogger(__name__)

if sys.platform == "win32":
    import spnego  # type: ignore
else:
    import gssapi  # type: ignore


class NegotiateClient:
    def __init__(self, *, hostname: str, service: str = "HTTP") -> None:
        log.info("Creating Negotiate client: service=%s hostname=%s", service, hostname)

        if sys.platform == "win32":
            spnego_kwargs: dict[str, object] = {}
            context_req = getattr(spnego, "ContextReq", None)
            if context_req is not None:
                request_flags = getattr(context_req, "default", None)
                for flag_name in ("mutual_auth", "delegate"):
                    flag_value = getattr(context_req, flag_name, None)
                    if flag_value is not None:
                        request_flags = flag_value if request_flags is None else request_flags | flag_value
                if request_flags is not None:
                    spnego_kwargs["context_req"] = request_flags

            self._ctx = spnego.client(
                hostname=hostname,
                service=service,
                protocol="negotiate",
                **spnego_kwargs,
            )
        else:
            svc_name = gssapi.Name(
                f"{service}@{hostname}",
                name_type=gssapi.NameType.hostbased_service,
            )
            self._ctx = gssapi.SecurityContext(
                name=svc_name,
                usage="initiate",
                flags=[
                    gssapi.RequirementFlag.mutual_authentication,
                    gssapi.RequirementFlag.delegate_to_peer,
                ],
            )

    @property
    def complete(self) -> bool:
        return bool(getattr(self._ctx, "complete", False))

    @property
    def initiator_name(self) -> str:
        if sys.platform == "win32":
            try:
                name = getattr(self._ctx, "client_principal", None)
                if name:
                    return str(name)
            except Exception:
                log.debug("Win32: could not read client_principal", exc_info=True)
            return ""
        
        try:
            cred = gssapi.Credentials(usage="initiate")
            if cred.name is not None:
                result = str(cred.name)
                if result:
                    return result
        except Exception:
            log.debug("gssapi.Credentials fallback failed", exc_info=True)

        try:
            ctx_name = getattr(self._ctx, "initiator_name", None)
            if ctx_name is not None:
                result = str(ctx_name)
                if result:
                    return result
        except Exception:
            log.debug("ctx.initiator_name str() failed", exc_info=True)

        try:
            import subprocess
            proc = subprocess.run(
                ["klist"], capture_output=True, text=True, timeout=3,
            )
            for line in proc.stdout.splitlines():
                line = line.strip()
                if line.lower().startswith("default principal:"):
                    principal = line.split(":", 1)[1].strip()
                    if principal:
                        return principal
        except Exception:
            log.debug("klist fallback failed", exc_info=True)

        return ""

    def step(self, in_token_b64: str) -> tuple[str, bool]:
        in_token = base64.b64decode(in_token_b64) if in_token_b64 else None
        out_token = self._ctx.step(in_token)
        out_b64 = base64.b64encode(out_token or b"").decode()

        log.debug(
            "Negotiate client step: in_len=%d out_len=%d complete=%s",
            len(in_token_b64 or ""),
            len(out_b64),
            self.complete,
        )
        return out_b64, self.complete