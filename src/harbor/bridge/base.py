from typing import Optional, Protocol

from harbor.core.models import HarborRequest


class HarborBridge(Protocol):
    def receive(self) -> Optional[HarborRequest]:
        ...
