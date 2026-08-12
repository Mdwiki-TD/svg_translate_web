from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class SharedMap:
    error: str | None = None

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FileLanguagesMap(SharedMap):
    """Result of extracting available SVG translation languages for a Commons file."""

    langs: list[str] | None = None


@dataclass
class FileInfo(SharedMap):
    imageinfo: list[dict[str, Any]] | None = None
    exists: bool | None = None


@dataclass
class DownloadAndSaveData(SharedMap):
    result: str
    path: str | None = None
    size_bytes: int | None = None


@dataclass
class DownloadResult(SharedMap):
    success: bool = False
    size_bytes: int | None = None
    path: str | None = None


@dataclass
class UploadResult(SharedMap):
    ok: bool | None
    error_details: str = ""
    msg: str | None = None
    result: dict[str, Any] | None = None

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


__all__ = [
    "FileLanguagesMap",
    "FileInfo",
    "DownloadAndSaveData",
    "DownloadResult",
    "UploadResult",
]
