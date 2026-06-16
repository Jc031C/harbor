import unittest

from harbor.bridges.base_bridge import BridgeInput
from harbor.core.config import load_config
from harbor.core.router import Router
from harbor.main import handle_bridge_input
from harbor.services.permission_service import PermissionService


class FakeLogger:
    def info(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass


class TestHarborMainFlow(unittest.TestCase):
    def setUp(self):
        self.config = load_config()
        self.router = Router(self.config)
        self.permission_service = PermissionService(self.config)
        self.logger = FakeLogger()

    def handle_text(self, raw_text: str, sender: str = "developer"):
        bridge_input = BridgeInput(
            source="mock_bridge",
            sender=sender,
            raw_text=raw_text,
        )

        return handle_bridge_input(
            bridge_input=bridge_input,
            router=self.router,
            permission_service=self.permission_service,
            logger=self.logger,
        )

    def test_mock_command(self):
        result = self.handle_text("/mock hello harbor")

        self.assertTrue(result.success)
        self.assertEqual(result.worker_name, "mock_worker")
        self.assertIn("hello harbor", result.message)

    def test_help_command(self):
        result = self.handle_text("/help")

        self.assertTrue(result.success)
        self.assertEqual(result.worker_name, "system_worker")
        self.assertIn("可用命令", result.message)
        self.assertNotIn("v0.1", result.message)

    def test_status_command(self):
        result = self.handle_text("/status")

        self.assertTrue(result.success)
        self.assertEqual(result.worker_name, "system_worker")
        self.assertIn("运行中", result.message)

    def test_gpt_command_placeholder(self):
        result = self.handle_text("/gpt 测试内容")

        self.assertTrue(result.success)
        self.assertEqual(result.worker_name, "gpt_desktop_worker")
        self.assertIn("占位回复", result.message)
        self.assertIn("测试内容", result.message)
        self.assertNotIn("v0.1", result.message)

    def test_unknown_command(self):
        result = self.handle_text("/abc hello")

        self.assertFalse(result.success)
        self.assertEqual(result.worker_name, "system_worker")
        self.assertIn("未知命令", result.message)
        self.assertNotIn("v0.1", result.message)

    def test_permission_denied_for_non_whitelist_sender(self):
        result = self.handle_text(
            raw_text="/mock hello harbor",
            sender="unknown-user",
        )

        self.assertFalse(result.success)
        self.assertEqual(result.worker_name, "permission_service")
        self.assertIn("权限拒绝", result.message)
        self.assertNotIn("v0.1", result.message)


if __name__ == "__main__":
    unittest.main()
