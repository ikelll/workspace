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
from src.ssl_trust import (
    CertificateChangedError,
    SslTrustStore,
    connect_with_trust,
    create_pinned_context,
    create_verified_context,
    fetch_certificate_info,
    verify_pinned_peer,
)
from src.transport import consts as tc
from src.transport.tools import get_cacerts_file
from src.utils.types import ForwardState

log = logging.getLogger(__name__)
_trust_store = SslTrustStore()

_ACTIVE_FORWARD_SERVERS: weakref.WeakSet[ForwardServer] = weakref.WeakSet()
_ACTIVE_LOCK = threading.Lock()


def take_all() -> list["ForwardServer"]:
    with _ACTIVE_LOCK:
        servers = list(_ACTIVE_FORWARD_SERVERS)
        _ACTIVE_FORWARD_SERVERS.clear()
    return servers


def stop_servers(servers: typing.Iterable["ForwardServer"]) -> None:
    for fs in servers:
        try:
            fs.stop()
            with contextlib.suppress(Exception):
                fs.server_close()
            t = getattr(fs, "_thread", None)
            if t is not None and getattr(t, "is_alive", lambda: False)():
                t.join(timeout=2)
        except Exception as e:
            log.debug("Error stopping tunnel: %s", e)


def stop_all() -> None:
    stop_servers(take_all())


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
        self._state_lock = threading.RLock()
        self.current_connections = 0
        self.status = ForwardState.TUNNEL_LISTENING
        self.can_stop = False

        timeout = timeout or 600
        self.timer = threading.Timer(
            timeout, ForwardServer._set_stoppable, args=(self,)
        )
        self.timer.start()

        log.debug(
            "ForwardServer: remote=%s ipv6=%s cert=%s keep=%s timeout=%d",
            remote,
            self.remote_ipv6,
            check_certificate,
            keep_listening,
            timeout,
        )

    def stop(self) -> None:
        with self._state_lock:
            if self.stop_flag.is_set():
                return
            self.stop_flag.set()
            timer, self.timer = self.timer, None
        log.debug("Stopping ForwardServer %s", self.server_address)
        if timer:
            timer.cancel()
        serve_thread = getattr(self, "_thread", None)
        if (
            serve_thread is not None
            and serve_thread.is_alive()
            and threading.current_thread() is not serve_thread
        ):
            with contextlib.suppress(Exception):
                self.shutdown()
        with contextlib.suppress(Exception):
            self.server_close()

    def _acquire_connection(self) -> int:
        with self._state_lock:
            self.current_connections += 1
            return self.current_connections

    def _release_connection(self) -> int:
        with self._state_lock:
            self.current_connections -= 1
            return self.current_connections

    def _stop_if_idle(self) -> None:
        with self._state_lock:
            should_stop = self.current_connections <= 0 and self.can_stop
        if should_stop:
            log.info("No more connections — stopping server")
            self.stop()

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
        count = self._acquire_connection()
        log.debug("Opening tunnel connection (connections=%d)", count)
        try:
            with self.connection() as ssl_socket:
                ForwardServer._open_tunnel(ssl_socket, self.ticket)
                yield ssl_socket
        finally:
            self._release_connection()

    @property
    def stoppable(self) -> bool:
        return self.can_stop

    @staticmethod
    def _set_stoppable(fs: ForwardServer) -> None:
        with fs._state_lock:
            fs.timer = None
            fs.can_stop = True
        fs._stop_if_idle()

    @staticmethod
    def _test(ssl_socket: ssl.SSLSocket) -> bool:
        try:
            ssl_socket.sendall(tc.CMD_TEST)
            resp = ssl_socket.recv(2)
            if resp != tc.RESPONSE_OK:
                raise ValueError(f"Invalid tunnel response: {resp}")
            log.debug("Tunnel is available")
            return True
        except ssl.SSLError as e:
            log.error("Certificate error: %s", e)
            raise RuntimeError(f"Certificate error: {e}") from e
        except Exception as e:
            log.error("Tunnel test failed: %s", e)
        return False

    @staticmethod
    def _open_tunnel(ssl_socket: ssl.SSLSocket, ticket: str) -> None:
        ssl_socket.sendall(tc.CMD_OPEN + ticket.encode())
        data = ssl_socket.recv(2)
        if data != tc.RESPONSE_OK:
            data += ssl_socket.recv(128)
            raise ConnectionError(f"Tunnel error: {data.decode(errors='ignore')}")

    @staticmethod
    def _connect(
        remote_addr: typing.Tuple[str, int],
        use_ipv6: bool = False,
        check_certificate: bool = True,
    ) -> ssl.SSLSocket:
        host, port = remote_addr
        family = socket.AF_INET6 if use_ipv6 else socket.AF_INET

        def _wrap(context: ssl.SSLContext) -> ssl.SSLSocket:
            rsocket = socket.socket(family, socket.SOCK_STREAM)
            try:
                log.info("CONNECT to %s", remote_addr)
                rsocket.connect(remote_addr)
                rsocket.sendall(tc.HANDSHAKE_V1)
                return context.wrap_socket(rsocket, server_hostname=host)
            except Exception:
                rsocket.close()
                raise

        if not check_certificate:
            log.warning("Tunnel certificate verification disabled by transport for %s", remote_addr)
            return _wrap(create_pinned_context(minimum_version=ssl.TLSVersion.TLSv1_3))

        def _verified() -> ssl.SSLSocket:
            return _wrap(
                create_verified_context(
                    cafile=get_cacerts_file(),
                    minimum_version=ssl.TLSVersion.TLSv1_3,
                )
            )

        def _pinned(fingerprint: str) -> ssl.SSLSocket:
            sock = _wrap(create_pinned_context(minimum_version=ssl.TLSVersion.TLSv1_3))
            try:
                verify_pinned_peer(sock, fingerprint)
            except Exception:
                sock.close()
                raise
            return sock

        return connect_with_trust(
            host,
            port,
            _trust_store,
            attempt_verified=_verified,
            attempt_pinned=_pinned,
            fetch_cert=lambda: fetch_certificate_info(
                host, port, server_hostname=host, prefix=tc.HANDSHAKE_V1, family=family
            ),
            prompt=lambda cert, errors, changed: confirm_certificate(
                None, cert, errors, changed=changed
            ),
        )


class Handler(socketserver.BaseRequestHandler):
    server: ForwardServer  # type: ignore[assignment]

    def handle(self) -> None:
        server = self.server
        with server._state_lock:
            if server.status == ForwardState.TUNNEL_LISTENING:
                server.status = ForwardState.TUNNEL_OPENING
            reject = server.stoppable and not server.keep_listening

        if reject:
            log.error("Rejected connection — timeout exceeded")
            self.request.close()
            return

        try:
            with server.open_tunnel() as ssl_socket:
                self._relay(ssl_socket)
        except (ssl.SSLCertVerificationError, CertificateChangedError) as e:
            log.error("Tunnel certificate rejected → %s: %s", server.remote, e)
            server.status = ForwardState.TUNNEL_ERROR
            server.stop()
        except Exception as e:
            log.error("Tunnel connection error → %s: %s", server.remote, e)
            with contextlib.suppress(Exception):
                self.request.close()
            if not server.keep_listening:
                server.status = ForwardState.TUNNEL_ERROR
                server.stop()

        server._stop_if_idle()

    def _relay(self, remote: ssl.SSLSocket) -> None:
        self.server.status = ForwardState.TUNNEL_PROCESSING
        log.debug("Relaying tunnel connection")
        try:
            readables = [self.request, remote]
            while not self.server.stop_flag.is_set():
                readable, _, exceptional = select.select(readables, [], readables, 1)
                for err in exceptional:
                    raise OSError(f"Error on connection: {err}")

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
                    while remote.pending():
                        data = remote.recv(tc.BUFFER_SIZE)
                        if not data:
                            return
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
    with _ACTIVE_LOCK:
        _ACTIVE_FORWARD_SERVERS.add(fs)
    _run(fs)
    return fs
