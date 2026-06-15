from typing import Protocol

from harbor.core.task import Task, WorkerResult


class BaseWorker(Protocol):
    name: str

    def handle(self, task: Task) -> WorkerResult:
        ...
