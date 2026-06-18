import json
import tempfile
import unittest
from pathlib import Path

from harbor.core.config import load_config
from harbor.core.config import HarborConfig
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


class TestHarborConfig(unittest.TestCase):
    def test_load_config_reads_utf8_bom_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "settings.json"
            payload = {
                "app": {"name": "Harbor", "version": "0.3.3-dev"},
                "wechat": {"mode": "Listen"},
            }
            config_path.write_text(
                json.dumps(payload, ensure_ascii=False),
                encoding="utf-8-sig",
            )

            config = load_config(config_path)

        self.assertEqual(config.app_name, "Harbor")
        self.assertEqual(config.wechat_mode, "listen")

    def test_wechat_mode_is_normalized(self):
        cases = [
            (" send_only ", "send_only"),
            ("Listen", "listen"),
            ("", "send_only"),
        ]

        for raw_mode, expected_mode in cases:
            with self.subTest(raw_mode=raw_mode):
                config = HarborConfig(settings={"wechat": {"mode": raw_mode}})

                self.assertEqual(config.wechat_mode, expected_mode)


if __name__ == "__main__":
    unittest.main()
