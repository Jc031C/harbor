from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class HarborRequest:
    source: str
    sender: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class HarborResponse:
    text: str
    handled_by: str = "harbor-core"
    success: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
