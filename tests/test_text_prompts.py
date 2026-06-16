from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestTextPrompts(unittest.TestCase):
    def test_user_facing_prompts_do_not_pin_v0_1(self):
        prompt_files = [
            PROJECT_ROOT / "src" / "harbor" / "workers" / "system_worker.py",
            PROJECT_ROOT / "src" / "harbor" / "services" / "permission_service.py",
            PROJECT_ROOT / "src" / "harbor" / "workers" / "gpt_desktop_worker.py",
            PROJECT_ROOT / "src" / "harbor" / "bridges" / "mock_bridge.py",
        ]

        for prompt_file in prompt_files:
            with self.subTest(path=prompt_file):
                content = prompt_file.read_text(encoding="utf-8")
                self.assertNotIn("v0.1", content)
                self.assertNotIn("Harbor v0.1", content)


if __name__ == "__main__":
    unittest.main()
