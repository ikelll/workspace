from __future__ import annotations

import atexit
import contextlib
import logging
import select
import socket
import socketserver
import ssl
import threading
import typing
import weakref

from src.dialogs.app_dialogs import confirm_certificate
from src.ssl_trust import SslTrustStore, fetch_certificate_info
from src.transport import consts as tc
from src.transport.tools import get_cacerts_file
from src.utils.types import ForwardState

log = logging.getLogger(__name__)
_trust_store = SslTrustStore()

_ACTIVE_FORWARD_SERVERS: weakref.WeakSet[ForwardServer] = weakref.WeakSet()


def stop_all() -> None:
    for fs in list(_ACTIVE_FORWARD_SERVERS):
        try:
            fs.stop()
            with contextlib.suppress(Exception):
                fs.server_close()
            t = getattr(fs, "_thread", None)
            if t is not None and getattr(t, "is_alive", lambda: False)():
                t.join(timeout=2)
        except Exception as e:
            log.debug("Error stopping tunnel: %s", e)


atexit.register(stop_all)


class ForwardServer(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

    remote: typing.Tuple[str, int]
    remote_ipv6: bool
    ticket: str
    stop_flag: threading.Event
    can_stop: bool
    timer: typing.Optional[threading.Timer]
    check_certificate: bool
    keep_listening: bool
    current_connections: int
    status: ForwardState

    address_family = socket.AF_INET

    def __init__(
        self,
        remote: typing.Tuple[str, int],
        ticket: str,
        timeout: int = 0,
        local_port: int = 0,
        check_certificate: bool = True,
        keep_listening: bool = False,
        ipv6_listen: bool = False,
        ipv6_remote: bool = False,
    ) -> None:
        if timeout < 0:
            keep_listening = True
            timeout = abs(timeout)

        if ipv6_listen:
            self.address_family = socket.AF_INET6

        super().__init__(
            server_address=(
                tc.LISTEN_ADDRESS_V6 if ipv6_listen else tc.LISTEN_ADDRESS,
                local_port,
            ),
            RequestHandlerClass=Handler,
        )

        self.remote = remote
        self.remote_ipv6 = ipv6_remote or ":" in remote[0]
        self.ticket = ticket
        self.check_certificate = check_certificate
        self.keep_listening = keep_listening
        self.stop_flag = threading.Event()
        self.current_connections = 0
        self.status = ForwardState.TUNNEL_LISTENING
        self.can_stop = False

        timeout = timeout or 60
        self.timer = threading.Timer(
            timeout, ForwardServer._set_stoppable, args=(self,)
        )
        self.timer.start()

        log.debug(
            "ForwardServer: remote=%s ipv6=%s ticket=%s… cert=%s keep=%s timeout=%d",
            remote,
            self.remote_ipv6,
            ticket[:8],
            check_certificate,
            keep_listening,
            timeout,
        )

    def stop(self) -> None:
        if not self.stop_flag.is_set():
            log.debug("Stopping ForwardServer %s", self.server_address)
            self.stop_flag.set()
            if self.timer:
                self.timer.cancel()
                self.timer = None
            self.shutdown()
            with contextlib.suppress(Exception):
                self.server_close()

    @contextlib.contextmanager
    def connection(self) -> typing.Generator[ssl.SSLSocket, None, None]:
        ssl_sock: typing.Optional[ssl.SSLSocket] = None
        try:
            ssl_sock = ForwardServer._connect(
                self.remote,
                self.remote_ipv6,
                self.check_certificate,
            )
            yield ssl_sock
        finally:
            if ssl_sock:
                ssl_sock.close()

    def check(self) -> bool:
        if self.status == ForwardState.TUNNEL_ERROR:
            return False
        with self.connection() as ssl_socket:
            return ForwardServer._test(ssl_socket)

    @contextlib.contextmanager
    def open_tunnel(self) -> typing.Generator[ssl.SSLSocket, None, None]:
        self.current_connections += 1
        log.debug(
            "Opening tunnel ticket=%s… connections=%d",
            self.ticket[:8],
            self.current_connections,
        )
        try:
            with self.connection() as ssl_socket:
                ForwardServer._open_tunnel(ssl_socket, self.ticket)
                yield ssl_socket
        except ssl.SSLError as e:
            log.error("Certificate error → %s: %s", self.remote, e)
            self.status = ForwardState.TUNNEL_ERROR
            self.stop()
        except Exception as e:
            log.error("Tunnel error → %s: %s", self.remote, e)
            self.status = ForwardState.TUNNEL_ERROR
            self.stop()
        finally:
            self.current_connections -= 1

    @property
    def stoppable(self) -> bool:
        return self.can_stop

    @staticmethod
    def _set_stoppable(fs: ForwardServer) -> None:
        fs.timer = None
        fs.can_stop = True
        if fs.current_connections <= 0:
            fs.stop()

    @staticmethod
    def _test(ssl_socket: ssl.SSLSocket) -> bool:
        try:
            ssl_socket.sendall(tc.CMD_TEST)
            resp = ssl_socket.recv(2)
            if resp != tc.RESPONSE_OK:
                raise Exception(f"Invalid tunnel response: {resp}")
            log.debug("Tunnel is available")
            return True
        except ssl.SSLError as e:
            log.error("Certificate error: %s", e)
            raise Exception(f"Certificate error: {e}") from e
        except Exception as e:
            log.error("Tunnel test failed: %s", e)
        return False

    @staticmethod
    def _open_tunnel(ssl_socket: ssl.SSLSocket, ticket: str) -> None:
        ssl_socket.sendall(tc.CMD_OPEN + ticket.encode())
        data = ssl_socket.recv(2)
        if data != tc.RESPONSE_OK:
            data += ssl_socket.recv(128)
            raise Exception(f"Tunnel error: {data.decode(errors='ignore')}")

    @staticmethod
    def _connect(
        remote_addr: typing.Tuple[str, int],
        use_ipv6: bool = False,
        check_certificate: bool = True,
    ) -> ssl.SSLSocket:
        host, port = remote_addr
        if _trust_store.is_trusted(host, port):
            check_certificate = False

        def _wrap_socket(allow_unverified: bool) -> ssl.SSLSocket:
            family = socket.AF_INET6 if use_ipv6 else socket.AF_INET
            rsocket = socket.socket(family, socket.SOCK_STREAM)
            try:
                log.info("CONNECT to %s", remote_addr)
                rsocket.connect(remote_addr)
                rsocket.sendall(tc.HANDSHAKE_V1)

                context = ssl.create_default_context()
                context.options |= ssl.OP_NO_COMPRESSION
                context.minimum_version = ssl.TLSVersion.TLSv1_3

                cacerts = get_cacerts_file()
                if cacerts is not None:
                    context.load_verify_locations(cacerts)

                if allow_unverified:
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    log.warning("Certificate checking disabled")

                return context.wrap_socket(rsocket, server_hostname=host)
            except Exception:
                rsocket.close()
                raise

        try:
            return _wrap_socket(not check_certificate)
        except ssl.SSLCertVerificationError as exc:
            cert = fetch_certificate_info(host, port, server_hostname=host)
            should_trust = confirm_certificate(None, cert, [str(exc)])
            if not should_trust:
                raise
            _trust_store.remember(host, port, cert)
            return _wrap_socket(True)


class Handler(socketserver.BaseRequestHandler):
    server: ForwardServer  # type: ignore[assignment]

    def handle(self) -> None:
        if self.server.status == ForwardState.TUNNEL_LISTENING:
            self.server.status = ForwardState.TUNNEL_OPENING

        if self.server.stoppable and not self.server.keep_listening:
            self.server.status = ForwardState.TUNNEL_ERROR
            log.error("Rejected connection — timeout exceeded")
            self.request.close()
            return

        try:
            with self.server.open_tunnel() as ssl_socket:
                self._relay(ssl_socket)
        except ssl.SSLError as e:
            log.error("SSL error: %s", e)
            self.server.status = ForwardState.TUNNEL_ERROR
            self.server.stop()
        except Exception as e:
            log.error("Tunnel relay error: %s", e)
            self.server.status = ForwardState.TUNNEL_ERROR
            self.server.stop()

        if self.server.current_connections <= 0 and self.server.stoppable:
            log.info("No more connections — stopping server")
            self.server.stop()

    def _relay(self, remote: ssl.SSLSocket) -> None:
        self.server.status = ForwardState.TUNNEL_PROCESSING
        log.debug("Relaying tunnel ticket=%s…", self.server.ticket[:8])
        try:
            readables = [self.request, remote]
            while not self.server.stop_flag.is_set():
                readable, _, exceptional = select.select(readables, [], readables, 1)
                for err in exceptional:
                    raise Exception(f"Error on connection: {err}")

                if self.request in readable:
                    data = self.request.recv(tc.BUFFER_SIZE)
                    if not data:
                        break
                    remote.sendall(data)

                if remote in readable:
                    data = remote.recv(tc.BUFFER_SIZE)
                    if not data:
                        break
                    self.request.sendall(data)
        except Exception as e:
            log.info("Relay closed: %s", e)
        finally:
            with contextlib.suppress(Exception):
                self.request.close()
            with contextlib.suppress(Exception):
                remote.close()


def _run(server: ForwardServer) -> None:
    def _runner() -> None:
        log.debug("Tunnel %s → %s serving", server.server_address, server.remote)
        server.serve_forever()
        log.debug("Tunnel %s → %s stopped", server.server_address, server.remote)

    t = threading.Thread(
        target=_runner,
        name=f"GorizontVS-Tunnel-{server.server_address[1]}",
        daemon=True,
    )
    server._thread = t  # type: ignore[attr-defined]
    t.start()


def forward(
    remote: typing.Tuple[str, int],
    ticket: str,
    timeout: int = 0,
    local_port: int = 0,
    check_certificate: bool = True,
    keep_listening: bool = True,
    use_ipv6: bool = False,
) -> ForwardServer:
    fs = ForwardServer(
        remote=remote,
        ticket=ticket,
        timeout=timeout,
        local_port=local_port,
        check_certificate=check_certificate,
        ipv6_remote=use_ipv6,
        keep_listening=keep_listening,
    )
    _ACTIVE_FORWARD_SERVERS.add(fs)
    _run(fs)
    return fs
