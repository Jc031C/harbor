import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from harbor.bridges import wechat_bridge
from harbor.bridges.wechat_bridge import (
    WeChatIncomingMessage,
    WeChatQueueAdapter,
    WeChatUnavailableError,
)
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


class FakeWxAutoClient:
    last_instance = None

    def __init__(self, *args, chat_name="JC", **kwargs):
        self.init_args = args
        self.init_kwargs = kwargs
        self.chat_name = chat_name
        self.chat_with_calls = []
        self.send_msg_calls = []
        self.show_calls = 0
        self.listen_calls = []
        FakeWxAutoClient.last_instance = self

    def ChatWith(self, contact_name, exact=True):
        self.chat_with_calls.append((contact_name, exact))
        return contact_name

    def ChatInfo(self):
        return {"chat_name": self.chat_name}

    def SendMsg(self, *args):
        self.send_msg_calls.append(args)

    def Show(self):
        self.show_calls += 1

    def AddListenChat(self, contact_name, callback):
        self.listen_calls.append((contact_name, callback))


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
                "app": {"name": "Harbor", "version": "0.3.2", "debug": True},
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
                    "mode": "send_only",
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

    def test_listen_allowed_text_message_writes_to_inbox(self):
        client = FakeWeChatClient(
            incoming_messages=[
                WeChatIncomingMessage(
                    sender_name="JC",
                    sender_id="wechat_JC",
                    content="/mock listen",
                )
            ]
        )

        written_count = self.adapter.process_listen_once(client)
        payload = self.read_single_inbox_payload()

        self.assertEqual(written_count, 1)
        self.assertEqual(payload["source"], "wechat")
        self.assertEqual(payload["sender_id"], "wechat_JC")
        self.assertEqual(payload["sender_name"], "JC")
        self.assertEqual(payload["message"], "/mock listen")

    def test_listen_rejects_non_allowed_sender(self):
        client = FakeWeChatClient(
            incoming_messages=[
                WeChatIncomingMessage(
                    sender_name="Stranger",
                    sender_id="wechat_Stranger",
                    content="/mock listen",
                )
            ]
        )

        written_count = self.adapter.process_listen_once(client)

        self.assertEqual(written_count, 0)
        self.assertEqual(list(self.inbox_path.glob("*.json")), [])

    def test_listen_rejects_when_allowed_senders_is_empty(self):
        self.adapter.allowed_senders = set()
        client = FakeWeChatClient(
            incoming_messages=[
                WeChatIncomingMessage(
                    sender_name="JC",
                    sender_id="wechat_JC",
                    content="/mock listen",
                )
            ]
        )

        written_count = self.adapter.process_listen_once(client)

        self.assertEqual(written_count, 0)
        self.assertEqual(list(self.inbox_path.glob("*.json")), [])

    def test_listen_duplicate_message_does_not_write_twice(self):
        message = WeChatIncomingMessage(
            sender_name="JC",
            sender_id="wechat_JC",
            content="/mock listen",
        )

        first_count = self.adapter.process_listen_once(FakeWeChatClient([message]))
        second_count = self.adapter.process_listen_once(FakeWeChatClient([message]))

        self.assertEqual(first_count, 1)
        self.assertEqual(second_count, 0)
        self.assertEqual(len(list(self.inbox_path.glob("*.json"))), 1)
        self.assertTrue((self.root_path / "wechat" / "listen_state.json").exists())

    def test_listen_skips_non_text_message(self):
        client = FakeWeChatClient(
            incoming_messages=[
                WeChatIncomingMessage(
                    sender_name="JC",
                    sender_id="wechat_JC",
                    content=None,
                )
            ]
        )

        written_count = self.adapter.process_listen_once(client)

        self.assertEqual(written_count, 0)
        self.assertEqual(list(self.inbox_path.glob("*.json")), [])

    def test_listen_does_not_send_or_process_outbox(self):
        result_path = self.write_outbox_result()
        client = FakeWeChatClient(
            incoming_messages=[
                WeChatIncomingMessage(
                    sender_name="JC",
                    sender_id="wechat_JC",
                    content="/mock listen",
                )
            ]
        )

        written_count = self.adapter.process_listen_once(client)

        self.assertEqual(written_count, 1)
        self.assertEqual(client.sent_messages, [])
        self.assertTrue(result_path.exists())
        self.assertFalse((self.sent_path / result_path.name).exists())
        self.assertFalse((self.failed_path / result_path.name).exists())

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

    def test_wechat_mode_defaults_to_send_only(self):
        config = HarborConfig(settings={})

        self.assertEqual(config.wechat_mode, "send_only")

    def test_wechat_mode_is_read_from_config(self):
        self.assertEqual(self.config.wechat_mode, "send_only")
        self.assertEqual(self.adapter.mode, "send_only")

    def test_wxauto_client_uses_loader(self):
        with patch.object(wechat_bridge, "load_wechat_client", return_value=FakeWxAutoClient):
            client = wechat_bridge.WxAutoWeChatClient(target_contact_name="JC")

        self.assertIsInstance(client.wx, FakeWxAutoClient)
        self.assertEqual(client.wx.init_kwargs, {"ads": False, "resize": False})
        self.assertEqual(client.wx.show_calls, 0)
        self.assertEqual(client.wx.listen_calls, [])

    def test_wxauto_client_can_enable_listener_for_listen_mode(self):
        with patch.object(wechat_bridge, "load_wechat_client", return_value=FakeWxAutoClient):
            client = wechat_bridge.WxAutoWeChatClient(
                target_contact_name="JC",
                enable_listener=True,
            )

        self.assertEqual(len(client.wx.listen_calls), 1)
        self.assertEqual(client.wx.listen_calls[0][0], "JC")
        self.assertTrue(client._listening)

    def test_wxauto_safe_send_checks_target_before_sending(self):
        with patch.object(wechat_bridge, "load_wechat_client", return_value=FakeWxAutoClient):
            client = wechat_bridge.WxAutoWeChatClient(target_contact_name="JC")

        client.send_message("JC", "hello")

        self.assertEqual(client.wx.chat_with_calls, [("JC", True)])
        self.assertEqual(client.wx.send_msg_calls, [("hello",)])
        self.assertEqual(client.wx.show_calls, 0)

    def test_wxauto_safe_send_rejects_target_mismatch(self):
        class MismatchFakeWxAutoClient(FakeWxAutoClient):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, chat_name="Other", **kwargs)

        with patch.object(wechat_bridge, "load_wechat_client", return_value=MismatchFakeWxAutoClient):
            client = wechat_bridge.WxAutoWeChatClient(target_contact_name="JC")

        with self.assertRaises(WeChatUnavailableError):
            client.send_message("JC", "hello")

        self.assertEqual(client.wx.chat_with_calls, [("JC", True)])
        self.assertEqual(client.wx.send_msg_calls, [])

    def test_send_only_without_replies_does_not_build_client(self):
        def build_client():
            raise AssertionError("client should not be built without pending replies")

        sent_count = self.adapter.process_send_only_once(build_client)

        self.assertEqual(sent_count, 0)

    def test_send_only_auto_reply_false_does_not_build_client(self):
        self.adapter.auto_reply = False
        self.write_outbox_result()

        def build_client():
            raise AssertionError("client should not be built when auto_reply=false")

        sent_count = self.adapter.process_send_only_once(build_client)

        self.assertEqual(sent_count, 0)

    def test_send_only_with_replies_builds_client_and_sends(self):
        result_path = self.write_outbox_result()
        client = FakeWeChatClient()
        build_calls = []

        def build_client():
            build_calls.append(True)
            return client

        sent_count = self.adapter.process_send_only_once(build_client)

        self.assertEqual(sent_count, 1)
        self.assertEqual(build_calls, [True])
        self.assertEqual(client.sent_messages, [("JC", "Mock Worker 已收到：hello harbor")])
        self.assertFalse(result_path.exists())
        self.assertTrue((self.sent_path / result_path.name).exists())

    def test_send_only_client_build_failure_moves_reply_to_failed(self):
        result_path = self.write_outbox_result()

        def build_client():
            raise WeChatUnavailableError("simulated unavailable")

        sent_count = self.adapter.process_send_only_once(build_client)

        self.assertEqual(sent_count, 0)
        self.assertFalse(result_path.exists())
        self.assertTrue((self.failed_path / result_path.name).exists())

    def test_main_exits_without_loading_client_when_wechat_disabled(self):
        with patch.object(wechat_bridge, "load_config", return_value=self.config):
            with patch.object(wechat_bridge, "build_default_wechat_client") as build_client:
                with redirect_stdout(io.StringIO()):
                    wechat_bridge.main()

        build_client.assert_not_called()

    def test_main_send_only_starts_without_eager_client_build(self):
        settings = dict(self.config.settings)
        settings["wechat"] = dict(settings["wechat"])
        settings["wechat"]["enabled"] = True
        settings["wechat"]["mode"] = "send_only"
        config = HarborConfig(settings=settings)

        with patch.object(wechat_bridge, "load_config", return_value=config):
            with patch.object(wechat_bridge.WeChatQueueAdapter, "run_send_only_forever") as run_send_only:
                with patch.object(wechat_bridge, "build_default_wechat_client") as build_client:
                    with redirect_stdout(io.StringIO()):
                        wechat_bridge.main()

        run_send_only.assert_called_once()
        build_client.assert_not_called()

    def test_main_listen_mode_keeps_eager_client_build(self):
        settings = dict(self.config.settings)
        settings["wechat"] = dict(settings["wechat"])
        settings["wechat"]["enabled"] = True
        settings["wechat"]["mode"] = "listen"
        config = HarborConfig(settings=settings)
        fake_client = FakeWeChatClient()

        with patch.object(wechat_bridge, "load_config", return_value=config):
            with patch.object(wechat_bridge, "build_default_wechat_client", return_value=fake_client) as build_client:
                with patch.object(wechat_bridge.WeChatQueueAdapter, "run_listen_forever") as run_listen:
                    with redirect_stdout(io.StringIO()):
                        wechat_bridge.main()

        build_client.assert_called_once_with(config)
        run_listen.assert_called_once_with(fake_client)


if __name__ == "__main__":
    unittest.main()
