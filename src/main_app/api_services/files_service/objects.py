from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class SharedMapToJson:
    def to_json(self) -> dict[str, Any]:
        return asdict(self)  # pyright: ignore[reportCallIssue]


@dataclass
class FileData(SharedMapToJson):
    file_name: str
    file_path: Path
    summary: str | None = None
    description: str | None = None
    new_file: bool = False

    def __post_init__(self) -> None:
        if self.file_name:
            self.file_name = self.fix_file_name(self.file_name)

    @classmethod
    def from_dict(cls, **data: dict[str, Any]) -> "FileData":
        return cls(
            file_name=data["file_name"],
            file_path=data["file_path"],
            summary=data.get("summary"),
            description=data.get("description"),
            new_file=data.get("new_file", False),
        )


    def fix_file_name(self, file_name: str) -> str:
        file_name = file_name.strip()
        if file_name.lower().startswith("file:"):
            file_name = file_name[5:].lstrip()
        return file_name

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
