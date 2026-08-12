from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class FileLanguagesMap:
    """Result of extracting available SVG translation languages for a Commons file."""

    error: str | None = None
    langs: list[str] | None = None


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


@dataclass
class UploadResult:
    ok: bool | None
    error: str | None = None
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
