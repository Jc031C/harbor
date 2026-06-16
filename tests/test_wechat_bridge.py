import json
import tempfile
import unittest
from pathlib import Path

from harbor.bridges.wechat_bridge import WeChatIncomingMessage, WeChatQueueAdapter
from harbor.core.config import HarborConfig


class FakeWeChatClient:
    def __init__(self, incoming_messages=None, fail_send=False):
        self.incoming_messages = list(incoming_messages or [])
        self.fail_send = fail_send
        self.sent_messages = []

    def get_messages(self):
        messages = list(self.incoming_messages)
        self.incoming_messages.clear()
        return messages

    def send_message(self, contact_name, content):
        if self.fail_send:
            raise RuntimeError("simulated send failure")
        self.sent_messages.append((contact_name, content))


class TestWeChatQueueAdapter(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root_path = Path(self.temp_dir.name)
        self.inbox_path = self.root_path / "inbox"
        self.outbox_path = self.root_path / "outbox"
        self.sent_path = self.root_path / "wechat" / "sent"
        self.failed_path = self.root_path / "wechat" / "failed"
        self.logs_path = self.root_path / "wechat" / "logs"

        self.config = HarborConfig(
            settings={
                "app": {"name": "Harbor", "version": "0.3.1", "debug": True},
                "bridge": {
                    "default": "local_queue",
                    "enabled": ["mock", "local_queue", "wechat_queue_adapter"],
                },
                "local_queue": {
                    "enabled": True,
                    "inbox_path": str(self.inbox_path),
                    "outbox_path": str(self.outbox_path),
                    "processed_path": str(self.root_path / "processed"),
                    "failed_path": str(self.root_path / "failed"),
                },
                "wechat": {
                    "enabled": False,
                    "target_contact_name": "",
                    "allowed_senders": ["JC"],
                    "poll_interval_seconds": 2,
                    "reply_check_interval_seconds": 2,
                    "auto_reply": True,
                    "sent_path": str(self.sent_path),
                    "failed_path": str(self.failed_path),
                    "logs_path": str(self.logs_path),
                },
                "workers": {"enabled": ["mock_worker", "system_worker"]},
                "permission": {"whitelist": ["JC"]},
                "logs": {
                    "path": str(self.root_path / "logs" / "harbor.log"),
                    "error_path": str(self.root_path / "logs" / "errors.log"),
                },
            }
        )

        self.adapter = WeChatQueueAdapter.from_config(self.config)

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_outbox_result(
        self,
        filename="wechat_result.json",
        receiver_name="JC",
        source="wechat",
        receiver_id=None,
    ):
        self.outbox_path.mkdir(parents=True, exist_ok=True)
        result_path = self.outbox_path / filename
        payload = {
            "task_id": "task_001",
            "source": source,
            "receiver_id": receiver_id if receiver_id is not None else f"wechat_{receiver_name}",
            "receiver_name": receiver_name,
            "success": True,
            "content": "Mock Worker 已收到：hello harbor",
            "created_at": "2026-06-15 10:00:00",
        }
        with result_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
        return result_path

    def write_legacy_outbox_result(self, filename="legacy_wechat_result.json"):
        result_path = self.write_outbox_result(filename=filename, source="wechat")
        with result_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        payload.pop("source")
        with result_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
        return result_path

    def read_single_inbox_payload(self):
        inbox_files = sorted(self.inbox_path.glob("*.json"))
        self.assertEqual(len(inbox_files), 1)
        with inbox_files[0].open("r", encoding="utf-8") as file:
            return json.load(file)

    def test_allowed_wechat_message_writes_to_inbox(self):
        client = FakeWeChatClient(
            incoming_messages=[
                WeChatIncomingMessage(
                    sender_name="JC",
                    sender_id="wechat_JC",
                    content="/mock hello harbor",
                )
            ]
        )

        written_count = self.adapter.process_incoming_once(client)
        payload = self.read_single_inbox_payload()

        self.assertEqual(written_count, 1)
        self.assertEqual(payload["source"], "wechat")
        self.assertEqual(payload["sender_id"], "wechat_JC")
        self.assertEqual(payload["sender_name"], "JC")
        self.assertEqual(payload["message"], "/mock hello harbor")
        self.assertTrue(payload["created_at"])

    def test_non_whitelisted_sender_is_ignored(self):
        client = FakeWeChatClient(
            incoming_messages=[
                WeChatIncomingMessage(
                    sender_name="Stranger",
                    sender_id="wechat_Stranger",
                    content="/mock hello harbor",
                )
            ]
        )

        written_count = self.adapter.process_incoming_once(client)

        self.assertEqual(written_count, 0)
        self.assertEqual(list(self.inbox_path.glob("*.json")), [])

    def test_outbox_result_can_be_collected_as_pending_reply(self):
        result_path = self.write_outbox_result()

        replies = self.adapter.collect_pending_replies()

        self.assertEqual(len(replies), 1)
        self.assertEqual(replies[0].path, result_path)
        self.assertEqual(replies[0].receiver_name, "JC")
        self.assertEqual(replies[0].receiver_id, "wechat_JC")
        self.assertIn("hello harbor", replies[0].content)

    def test_send_success_moves_result_to_sent(self):
        result_path = self.write_outbox_result()
        client = FakeWeChatClient()

        sent_count = self.adapter.process_outbox_once(client)

        self.assertEqual(sent_count, 1)
        self.assertEqual(client.sent_messages, [("JC", "Mock Worker 已收到：hello harbor")])
        self.assertFalse(result_path.exists())
        self.assertTrue((self.sent_path / result_path.name).exists())
        self.assertFalse((self.failed_path / result_path.name).exists())

    def test_send_failure_moves_result_to_failed(self):
        result_path = self.write_outbox_result()
        client = FakeWeChatClient(fail_send=True)

        sent_count = self.adapter.process_outbox_once(client)

        self.assertEqual(sent_count, 0)
        self.assertFalse(result_path.exists())
        self.assertFalse((self.sent_path / result_path.name).exists())
        self.assertTrue((self.failed_path / result_path.name).exists())

    def test_non_wechat_source_is_not_sent_or_moved(self):
        result_path = self.write_outbox_result(
            filename="local_queue_result.json",
            source="local_queue",
            receiver_id="wechat_JC",
        )
        client = FakeWeChatClient()

        sent_count = self.adapter.process_outbox_once(client)

        self.assertEqual(sent_count, 0)
        self.assertEqual(client.sent_messages, [])
        self.assertTrue(result_path.exists())
        self.assertFalse((self.sent_path / result_path.name).exists())
        self.assertFalse((self.failed_path / result_path.name).exists())

    def test_wechat_source_result_can_be_sent(self):
        result_path = self.write_outbox_result(source="wechat")
        client = FakeWeChatClient()

        sent_count = self.adapter.process_outbox_once(client)

        self.assertEqual(sent_count, 1)
        self.assertEqual(client.sent_messages, [("JC", "Mock Worker 已收到：hello harbor")])
        self.assertFalse(result_path.exists())
        self.assertTrue((self.sent_path / result_path.name).exists())

    def test_legacy_result_without_source_uses_wechat_receiver_id(self):
        result_path = self.write_legacy_outbox_result()
        client = FakeWeChatClient()

        sent_count = self.adapter.process_outbox_once(client)

        self.assertEqual(sent_count, 1)
        self.assertEqual(client.sent_messages, [("JC", "Mock Worker 已收到：hello harbor")])
        self.assertFalse(result_path.exists())
        self.assertTrue((self.sent_path / result_path.name).exists())

    def test_legacy_result_without_source_requires_wechat_receiver_id(self):
        result_path = self.write_legacy_outbox_result(filename="legacy_local_result.json")
        with result_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        payload["receiver_id"] = "jc_local"
        with result_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
        client = FakeWeChatClient()

        sent_count = self.adapter.process_outbox_once(client)

        self.assertEqual(sent_count, 0)
        self.assertEqual(client.sent_messages, [])
        self.assertTrue(result_path.exists())
        self.assertFalse((self.sent_path / result_path.name).exists())
        self.assertFalse((self.failed_path / result_path.name).exists())

    def test_wechat_unavailable_does_not_raise(self):
        written_count = self.adapter.process_incoming_once(wechat_client=None)
        sent_count = self.adapter.process_outbox_once(wechat_client=None)

        self.assertEqual(written_count, 0)
        self.assertEqual(sent_count, 0)
        self.assertTrue((self.logs_path / "wechat_bridge.log").exists())


if __name__ == "__main__":
    unittest.main()
