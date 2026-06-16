import json
import tempfile
import unittest
from pathlib import Path

from harbor.bridges.local_queue_bridge import LocalQueueBridge
from harbor.core.config import HarborConfig
from harbor.core.router import Router
from harbor.main import handle_bridge_input
from harbor.services.permission_service import PermissionService


class FakeLogger:
    def info(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass


class TestLocalQueueBridge(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root_path = Path(self.temp_dir.name)
        self.inbox_path = self.root_path / "inbox"
        self.outbox_path = self.root_path / "outbox"
        self.processed_path = self.root_path / "processed"
        self.failed_path = self.root_path / "failed"
        self.error_log_path = self.root_path / "logs" / "errors.log"

        self.config = HarborConfig(
            settings={
                "app": {
                    "name": "Harbor",
                    "version": "0.2.0",
                    "debug": True,
                },
                "bridge": {
                    "default": "local_queue",
                    "enabled": ["mock", "local_queue"],
                },
                "local_queue": {
                    "enabled": True,
                    "inbox_path": str(self.inbox_path),
                    "outbox_path": str(self.outbox_path),
                    "processed_path": str(self.processed_path),
                    "failed_path": str(self.failed_path),
                },
                "workers": {
                    "enabled": [
                        "mock_worker",
                        "system_worker",
                        "gpt_desktop_worker",
                    ]
                },
                "permission": {
                    "whitelist": ["JC"],
                },
                "gpt_desktop": {
                    "enabled": False,
                },
                "logs": {
                    "path": str(self.root_path / "logs" / "harbor.log"),
                    "error_path": str(self.error_log_path),
                },
            }
        )

        self.bridge = LocalQueueBridge.from_config(self.config)
        self.router = Router(self.config)
        self.permission_service = PermissionService(self.config)
        self.logger = FakeLogger()

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_inbox_json(self, filename: str, payload: dict):
        input_path = self.inbox_path / filename
        with input_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
        return input_path

    def process_all(self):
        return self.bridge.process_all(
            handler=lambda bridge_input: handle_bridge_input(
                bridge_input=bridge_input,
                router=self.router,
                permission_service=self.permission_service,
                logger=self.logger,
            )
        )

    def read_single_outbox_payload(self):
        outbox_files = sorted(self.outbox_path.glob("*.json"))
        self.assertEqual(len(outbox_files), 1)

        with outbox_files[0].open("r", encoding="utf-8") as file:
            return json.load(file)

    def test_valid_json_input_can_be_processed(self):
        self.write_inbox_json(
            "test_mock.json",
            {
                "source": "local_queue",
                "sender_id": "jc_local",
                "sender_name": "JC",
                "message": "/mock hello harbor",
            },
        )

        processed_count = self.process_all()

        self.assertEqual(processed_count, 1)

    def test_mock_command_generates_outbox_result(self):
        self.write_inbox_json(
            "test_mock.json",
            {
                "source": "local_queue",
                "sender_id": "jc_local",
                "sender_name": "JC",
                "message": "/mock hello harbor",
            },
        )

        self.process_all()
        payload = self.read_single_outbox_payload()

        self.assertTrue(payload["success"])
        self.assertEqual(payload["source"], "local_queue")
        self.assertEqual(payload["receiver_id"], "jc_local")
        self.assertEqual(payload["receiver_name"], "JC")
        self.assertIn("hello harbor", payload["content"])
        self.assertTrue(payload["task_id"])

    def test_wechat_source_is_preserved_in_outbox_result(self):
        self.write_inbox_json(
            "wechat_mock.json",
            {
                "source": "wechat",
                "sender_id": "wechat_JC",
                "sender_name": "JC",
                "message": "/mock hello harbor",
            },
        )

        self.process_all()
        payload = self.read_single_outbox_payload()

        self.assertTrue(payload["success"])
        self.assertEqual(payload["source"], "wechat")
        self.assertEqual(payload["receiver_id"], "wechat_JC")

    def test_successful_input_file_moves_to_processed(self):
        self.write_inbox_json(
            "test_mock.json",
            {
                "source": "local_queue",
                "sender_id": "jc_local",
                "sender_name": "JC",
                "message": "/mock hello harbor",
            },
        )

        self.process_all()

        self.assertFalse((self.inbox_path / "test_mock.json").exists())
        self.assertTrue((self.processed_path / "test_mock.json").exists())
        self.assertFalse((self.failed_path / "test_mock.json").exists())

    def test_invalid_json_moves_to_failed(self):
        input_path = self.inbox_path / "broken.json"
        input_path.write_text("{invalid json", encoding="utf-8")

        processed_count = self.process_all()

        self.assertEqual(processed_count, 1)
        self.assertFalse(input_path.exists())
        self.assertTrue((self.failed_path / "broken.json").exists())
        self.assertTrue(self.error_log_path.exists())
        self.assertIn("broken.json", self.error_log_path.read_text(encoding="utf-8"))

    def test_non_whitelisted_sender_name_is_rejected(self):
        self.write_inbox_json(
            "blocked.json",
            {
                "source": "local_queue",
                "sender_id": "blocked_local",
                "sender_name": "NotAllowed",
                "message": "/mock hello harbor",
            },
        )

        self.process_all()
        payload = self.read_single_outbox_payload()

        self.assertFalse(payload["success"])
        self.assertEqual(payload["worker_name"], "permission_service")
        self.assertIn("权限拒绝", payload["content"])
        self.assertTrue((self.failed_path / "blocked.json").exists())


if __name__ == "__main__":
    unittest.main()
