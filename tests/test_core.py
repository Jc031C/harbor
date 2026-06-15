import unittest

from harbor.core.engine import HarborCore
from harbor.core.models import HarborRequest


class TestHarborCore(unittest.TestCase):
    def setUp(self):
        self.core = HarborCore()

    def test_hello_message(self):
        request = HarborRequest(
            source="test",
            sender="tester",
            text="你好",
        )

        response = self.core.handle(request)

        self.assertTrue(response.success)
        self.assertIn("Harbor Core", response.text)
        self.assertEqual(response.handled_by, "harbor-core")

    def test_empty_message(self):
        request = HarborRequest(
            source="test",
            sender="tester",
            text="   ",
        )

        response = self.core.handle(request)

        self.assertFalse(response.success)
        self.assertIn("空消息", response.text)

    def test_status_message(self):
        request = HarborRequest(
            source="test",
            sender="tester",
            text="状态",
        )

        response = self.core.handle(request)

        self.assertTrue(response.success)
        self.assertIn("运行中", response.text)

    def test_help_message(self):
        request = HarborRequest(
            source="test",
            sender="tester",
            text="帮助",
        )

        response = self.core.handle(request)

        self.assertTrue(response.success)
        self.assertIn("当前可用指令", response.text)

    def test_mock_llm_message(self):
        request = HarborRequest(
            source="test",
            sender="tester",
            text="问 Harbor 是什么",
        )

        response = self.core.handle(request)

        self.assertTrue(response.success)
        self.assertEqual(response.handled_by, "mock-llm-connector")
        self.assertIn("Harbor 是什么", response.text)

    def test_unknown_message(self):
        request = HarborRequest(
            source="test",
            sender="tester",
            text="测试普通消息",
        )

        response = self.core.handle(request)

        self.assertTrue(response.success)
        self.assertIn("测试普通消息", response.text)


if __name__ == "__main__":
    unittest.main()
