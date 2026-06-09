import typing

from . import types
from .version import APP_VERSION

VERSION: typing.Final[str] = APP_VERSION
USER_AGENT: typing.Final[str] = f"GorizontVS/{VERSION} ({types.OsType.DETECTED_SO})"

BUFFER_SIZE: typing.Final[int] = 1024 * 16
LISTEN_ADDRESS: typing.Final[str] = '127.0.0.1'
LISTEN_ADDRESS_V6: typing.Final[str] = '::1'
RESPONSE_OK: typing.Final[bytes] = b'OK'