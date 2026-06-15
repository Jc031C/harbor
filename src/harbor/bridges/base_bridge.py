from dataclasses import dataclass
from typing import Optional, Protocol

from harbor.core.task import WorkerResult


@dataclass(frozen=True)
class BridgeInput:
    source: str
    sender: str
    raw_text: str


class BaseBridge(Protocol):
    def receive(self) -> Optional[BridgeInput]:
        ...

    def send_result(self, result: WorkerResult) -> None:
        ...
