from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class FileInfo:
    imageinfo: list[dict[str, Any]] | None = None
    error: str | None = None
    exists: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DownloadAndSaveData:
    result: str
    msg: str | None = None
    error: str | None = None
    path: str | None = None
    size_bytes: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DownloadResult:
    success: bool = False
    size_bytes: int | None = None
    path: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


__all__ = [
    "FileInfo",
    "DownloadAndSaveData",
    "DownloadResult",
]
