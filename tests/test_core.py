import unittest

from harbor.core.config import load_config
from harbor.core.router import Router
from harbor.core.task import build_task
from harbor.workers.gpt_desktop_worker import GPTDesktopWorker
from harbor.workers.mock_worker import MockWorker
from harbor.workers.system_worker import SystemWorker


class TestHarborCoreStandardFlow(unittest.TestCase):
    def setUp(self):
        self.config = load_config()
        self.router = Router(self.config)

    def test_build_task_from_mock_command(self):
        task = build_task(
            source="test",
            sender="developer",
            raw_text="/mock hello harbor",
        )

        self.assertEqual(task.command, "/mock")
        self.assertEqual(task.content, "hello harbor")

    def test_router_routes_mock_to_mock_worker(self):
        task = build_task(
            source="test",
            sender="developer",
            raw_text="/mock hello harbor",
        )

        worker = self.router.route(task)

        self.assertIsInstance(worker, MockWorker)

    def test_router_routes_gpt_to_gpt_desktop_worker(self):
        task = build_task(
            source="test",
            sender="developer",
            raw_text="/gpt 测试内容",
        )

        worker = self.router.route(task)

        self.assertIsInstance(worker, GPTDesktopWorker)

    def test_router_routes_help_to_system_worker(self):
        task = build_task(
            source="test",
            sender="developer",
            raw_text="/help",
        )

        worker = self.router.route(task)

        self.assertIsInstance(worker, SystemWorker)

    def test_router_routes_status_to_system_worker(self):
        task = build_task(
            source="test",
            sender="developer",
            raw_text="/status",
        )

        worker = self.router.route(task)

        self.assertIsInstance(worker, SystemWorker)

    def test_router_routes_unknown_to_system_worker(self):
        task = build_task(
            source="test",
            sender="developer",
            raw_text="/abc hello",
        )

        worker = self.router.route(task)

        self.assertIsInstance(worker, SystemWorker)


if __name__ == "__main__":
    unittest.main()
