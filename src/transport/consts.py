from __future__ import annotations

import typing

# ── RSA public key for verifying transport script signatures ──────────
PUBLIC_KEY: typing.Final[bytes] = b"""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvcoBDk4xdxQWMDMnc7cM
zWhDQbC/J7IIXPnPvy55yFKfiqLgM8QFfCzvFKTXQIRctVnnQICiy1jlAv34E7Qk
PGkFSLI6K6wCotXOKDtxrtBSU6efr2QzQc3demsv5NLVy9JwMXQXtqGHQLuiKnW+
m/i/ty5rVWY/U8lNXxGmZyB6ZT0iw6XrTKL/ndI85o0g2nv+KtxJIBRniF1U2+64
QePOl3K2qb9KYRJGw2PQPodU7jbYPGqf7bfrfFL+k/4EaWaXwjSj6Lx/p6XQ/znY
inDcB6vxbT0wEdd7tFi0HAQr75lf9pW6SrFM5Mmjmz9dxWk4AW2BhMOfmEmOjHQx
DwIDAQAB
-----END PUBLIC KEY-----"""

# ── Tunnel protocol constants ─────────────────────────────────────────
HANDSHAKE_V1: typing.Final[bytes] = b"\x5AMGB\xA5\x01\x00"
CMD_TEST: typing.Final[bytes] = b"TEST"
CMD_OPEN: typing.Final[bytes] = b"OPEN"
RESPONSE_OK: typing.Final[bytes] = b"OK"

BUFFER_SIZE: typing.Final[int] = 1024 * 16
LISTEN_ADDRESS: typing.Final[str] = "127.0.0.1"
LISTEN_ADDRESS_V6: typing.Final[str] = "::1"

TICKET_LENGTH: typing.Final[int] = 40

# TLS ciphers for the tunnel connection
SECURE_CIPHERS: typing.Final[str] = (
    "TLS_AES_256_GCM_SHA384"
    ":TLS_CHACHA20_POLY1305_SHA256"
    ":TLS_AES_128_GCM_SHA256"
    ":ECDHE-RSA-AES256-GCM-SHA384"
    ":ECDHE-RSA-AES128-GCM-SHA256"
    ":ECDHE-RSA-CHACHA20-POLY1305"
    ":ECDHE-ECDSA-AES128-GCM-SHA256"
    ":ECDHE-ECDSA-AES256-GCM-SHA384"
    ":ECDHE-ECDSA-CHACHA20-POLY1305"
)
