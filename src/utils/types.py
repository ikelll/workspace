import enum
import sys
import typing


class AuthenticatorType(typing.NamedTuple):
    authId: str
    authSmallName: str
    auth: str
    type: str
    priority: int
    isCustom: bool


class RemovableFile(typing.NamedTuple):
    path: str
    early_stage: bool = False


class AwaitableTask(typing.NamedTuple):
    task: typing.Any
    wait_subprocesses: bool = False


class OsType(enum.Enum):
    LINUX = "Linux"
    WINDOWS = "Windows"
    MACOS = "MacOS"
    UNKNOWN = "Unknown"

    DETECTED_SO = (
        LINUX
        if sys.platform.startswith("linux")
        else (
            WINDOWS
            if sys.platform.startswith("win")
            else MACOS
            if sys.platform.startswith("darwin")
            else UNKNOWN
        )
    )

    def __str__(self) -> str:
        return str(self.value)


class ForwardState(enum.IntEnum):
    TUNNEL_LISTENING = 0
    TUNNEL_OPENING = 1
    TUNNEL_PROCESSING = 2
    TUNNEL_ERROR = 3
