""" """

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RouteModule:
    route_cls: type
    name: str
    url_prefix: str = ""
    extra_kwargs: dict[str, Any] = field(default_factory=dict)
