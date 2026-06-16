import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from harbor.bridges.base_bridge import BridgeInput
from harbor.core.config import HarborConfig
from harbor.core.task import WorkerResult


class LocalQueueBridge:
    """Bridge that processes local JSON message files one batch at a time."""

    name = "local_queue"

    def __init__(
        self,
        inbox_path: str | Path = "data/inbox",
        outbox_path: str | Path = "data/outbox",
        processed_path: str | Path = "data/processed",
        failed_path: str | Path = "data/failed",
        error_log_path: str | Path = "data/logs/errors.log",
    ):
        self.inbox_path = Path(inbox_path)
        self.outbox_path = Path(outbox_path)
        self.processed_path = Path(processed_path)
        self.failed_path = Path(failed_path)
        self.error_log_path = Path(error_log_path)
        self._ensure_directories()

    @classmethod
    def from_config(cls, config: HarborConfig) -> "LocalQueueBridge":
        return cls(
            inbox_path=config.local_queue_inbox_path,
            outbox_path=config.local_queue_outbox_path,
            processed_path=config.local_queue_processed_path,
            failed_path=config.local_queue_failed_path,
            error_log_path=config.error_log_path,
        )

    def process_all(
        self,
        handler: Callable[[BridgeInput], WorkerResult],
    ) -> int:
        """Process all JSON files currently waiting in inbox, then return count."""
        processed_count = 0

        for input_path in sorted(self.inbox_path.glob("*.json")):
            if not input_path.is_file():
                continue

            self.process_one(input_path=input_path, handler=handler)
            processed_count += 1

        return processed_count

    def process_one(
        self,
        input_path: str | Path,
        handler: Callable[[BridgeInput], WorkerResult],
    ) -> WorkerResult | None:
        input_path = Path(input_path)
        payload: dict[str, Any] | None = None

        try:
            payload = self._read_payload(input_path)
            bridge_input = self._payload_to_bridge_input(payload, input_path)
            result = handler(bridge_input)

            self._write_result_file(
                input_path=input_path,
                payload=payload,
                result=result,
                task_id=bridge_input.metadata["task_id"],
            )

            if result.success:
                self._move_file(input_path, self.processed_path)
            else:
                self._move_file(input_path, self.failed_path)

            return result

        except Exception as exc:  # noqa: BLE001 - bridge must quarantine bad files.
            error_message = f"Local Queue 处理失败：{input_path.name}，原因：{exc}"
            self._append_error_log(error_message)
            self._write_error_file(
                input_path=input_path,
                payload=payload,
                error_message=error_message,
            )
            self._move_file(input_path, self.failed_path)
            return None

    def _ensure_directories(self) -> None:
        for path in [
            self.inbox_path,
            self.outbox_path,
            self.processed_path,
            self.failed_path,
            self.error_log_path.parent,
        ]:
            path.mkdir(parents=True, exist_ok=True)

    def _read_payload(self, input_path: Path) -> dict[str, Any]:
        with input_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        if not isinstance(payload, dict):
            raise ValueError("输入 JSON 顶层必须是对象。")

        return payload

    def _payload_to_bridge_input(
        self,
        payload: dict[str, Any],
        input_path: Path,
    ) -> BridgeInput:
        message = payload.get("message")
        sender_name = payload.get("sender_name")
        sender_id = payload.get("sender_id", "")
        created_at = payload.get("created_at") or self._now_text()
        task_id = payload.get("task_id") or uuid4().hex

        if not isinstance(message, str) or not message.strip():
            raise ValueError("字段 message 不能为空。")

        if not isinstance(sender_name, str) or not sender_name.strip():
            raise ValueError("字段 sender_name 不能为空。")

        return BridgeInput(
            source=str(payload.get("source") or self.name),
            sender=sender_name.strip(),
            raw_text=message.strip(),
            metadata={
                "task_id": task_id,
                "sender_id": sender_id,
                "sender_name": sender_name.strip(),
                "created_at": created_at,
                "input_file": input_path.name,
            },
        )

    def _write_result_file(
        self,
        input_path: Path,
        payload: dict[str, Any],
        result: WorkerResult,
        task_id: str,
    ) -> Path:
        output_payload = {
            "task_id": task_id,
            "source": str(payload.get("source") or self.name),
            "receiver_id": payload.get("sender_id", ""),
            "receiver_name": payload.get("sender_name", ""),
            "success": result.success,
            "content": result.message,
            "worker_name": result.worker_name,
            "created_at": self._now_text(),
        }

        output_path = self._unique_path(
            self.outbox_path / f"{input_path.stem}.result.json"
        )

        with output_path.open("w", encoding="utf-8") as file:
            json.dump(output_payload, file, ensure_ascii=False, indent=2)
            file.write("\n")

        return output_path

    def _write_error_file(
        self,
        input_path: Path,
        payload: dict[str, Any] | None,
        error_message: str,
    ) -> Path:
        payload = payload or {}
        output_payload = {
            "task_id": payload.get("task_id", uuid4().hex),
            "source": str(payload.get("source") or self.name),
            "receiver_id": payload.get("sender_id", ""),
            "receiver_name": payload.get("sender_name", ""),
            "success": False,
            "content": error_message,
            "worker_name": self.name,
            "created_at": self._now_text(),
        }

        output_path = self._unique_path(
            self.outbox_path / f"{input_path.stem}.error.json"
        )

        with output_path.open("w", encoding="utf-8") as file:
            json.dump(output_payload, file, ensure_ascii=False, indent=2)
            file.write("\n")

        return output_path

    def _move_file(self, input_path: Path, target_dir: Path) -> Path:
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = self._unique_path(target_dir / input_path.name)
        shutil.move(str(input_path), str(target_path))
        return target_path

    def _unique_path(self, path: Path) -> Path:
        if not path.exists():
            return path

        for index in range(1, 10_000):
            candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
            if not candidate.exists():
                return candidate

        raise FileExistsError(f"无法生成唯一文件名：{path}")

    def _append_error_log(self, message: str) -> None:
        self.error_log_path.parent.mkdir(parents=True, exist_ok=True)

        with self.error_log_path.open("a", encoding="utf-8") as file:
            file.write(f"{self._now_text()} | {message}\n")

    def _now_text(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
