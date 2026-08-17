from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class SharedMapToJson:
    def to_json(self) -> dict[str, Any]:
        return asdict(self)  # pyright: ignore[reportCallIssue]


@dataclass
class WriteData(SharedMapToJson):
    path: Path
    success: bool | None = None
    error: str | None = None


@dataclass
class FileLanguagesMap(SharedMapToJson):
    """Result of extracting available SVG translation languages for a Commons file."""

    langs: list[str] | None = None
    error: str | None = None


@dataclass
class FileInfo(SharedMapToJson):
    error: str | None = None
    imageinfo: list[dict[str, Any]] | None = None
    exists: bool | None = None


@dataclass
class DownloadAndSaveData(SharedMapToJson):
    result: str
    path: str | None = None
    size_bytes: int | None = None
    error: str | None = None


@dataclass
class DownloadResult(SharedMapToJson):
    success: bool | None = None
    size_bytes: int | None = None
    path: str | None = None
    error: str | None = None


@dataclass
class UploadResult(SharedMapToJson):
    ok: bool | None
    error_details: str = ""
    msg: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None


__all__ = [
    "FileLanguagesMap",
    "FileInfo",
    "WriteData",
    "DownloadAndSaveData",
    "DownloadResult",
    "UploadResult",
]
