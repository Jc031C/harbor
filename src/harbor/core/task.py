from dataclasses import dataclass, field
from typing import Any

from harbor.utils.text_utils import split_command


@dataclass(frozen=True)
class Task:
    source: str
    sender: str
    raw_text: str
    command: str
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkerResult:
    success: bool
    message: str
    worker_name: str
    metadata: dict[str, Any] = field(default_factory=dict)


def build_task(
    source: str,
    sender: str,
    raw_text: str,
    metadata: dict[str, Any] | None = None,
) -> Task:
    command, content = split_command(raw_text)

    return Task(
        source=source,
        sender=sender,
        raw_text=raw_text,
        command=command,
        content=content,
        metadata=metadata or {},
    )
