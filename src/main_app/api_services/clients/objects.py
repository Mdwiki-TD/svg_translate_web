from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class RawGrapherMetadataResponse:
    data: dict[str, Any] | None = None
    status_code: int | None = None


@dataclass
class SharedMapToJson:
    def to_json(self) -> dict[str, Any]:
        return asdict(self)  # pyright: ignore[reportCallIssue]


@dataclass
class GetWithRetryData(SharedMapToJson):
    content: str | None = None
    success: bool | None = None
    status_code: int | None = None
    msg: int | None = None
    attempts: int | None = None
    wait_time: int | None = None


__all__ = [
    "GetWithRetryData",
]
