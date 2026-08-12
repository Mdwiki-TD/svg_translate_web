from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class RawGrapherMetadataResponse:
    data: dict[str, Any] | None = None
    status_code: int | None = None


@dataclass
class ChartMetadata:
    title: str | None = None
    subtitle: str | None = None
    citation: str | None = None
    originalChartUrl: str | None = None
    selection: list[str] = field(default_factory=list)


@dataclass
class ColumnMetadata:
    titleShort: str | None = None
    titleLong: str | None = None
    shortUnit: str | None = None
    unit: str | None = None
    timespan: str | None = None
    type: str | None = None
    owidVariableId: int | None = None
    shortName: str | None = None
    lastUpdated: str | None = None
    citationShort: str | None = None
    citationLong: str | None = None
    fullMetadata: str | None = None


@dataclass
class GrapherMetadataResponse:
    chart: ChartMetadata | None = None
    columns: dict[str, ColumnMetadata] = field(default_factory=dict)
    dateDownloaded: str | None = None
    status_code: int | None = None

    @classmethod
    def from_dict(cls, data: dict | None, status_code: int | None) -> "GrapherMetadataResponse":
        if not data:
            return cls(status_code=status_code)

        chart_data = data.get("chart")
        chart_obj = ChartMetadata(**chart_data) if chart_data else None

        columns_data = data.get("columns", {})
        columns_obj = {key: ColumnMetadata(**val) for key, val in columns_data.items()}

        return cls(
            chart=chart_obj,
            columns=columns_obj,
            dateDownloaded=data.get("dateDownloaded"),
            status_code=status_code,
        )


@dataclass
class SharedMapToJson:
    def to_json(self) -> dict[str, Any]:
        return asdict(self)


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
