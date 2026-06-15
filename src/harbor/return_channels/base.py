from typing import Protocol

from harbor.core.models import HarborResponse


class HarborReturnChannel(Protocol):
    def send(self, response: HarborResponse) -> None:
        ...
