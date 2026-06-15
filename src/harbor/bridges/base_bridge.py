from dataclasses import dataclass, field
from typing import Any, Optional, Protocol

from harbor.core.task import WorkerResult


@dataclass(frozen=True)
class BridgeInput:
    source: str
    sender: str
    raw_text: str
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseBridge(Protocol):
    def receive(self) -> Optional[BridgeInput]:
        ...

    def send_result(self, result: WorkerResult) -> None:
        ...
