from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestWindowsScripts(unittest.TestCase):
    def test_start_wechat_bridge_bat_exists(self):
        script_path = PROJECT_ROOT / "scripts" / "start_wechat_bridge.bat"

        self.assertTrue(script_path.exists())

    def test_start_wechat_bridge_python_lookup_order(self):
        script_path = PROJECT_ROOT / "scripts" / "start_wechat_bridge.bat"
        content = script_path.read_text(encoding="utf-8")

        self.assertIn(r".\.venv\Scripts\python.exe", content)
        self.assertIn("where py", content)
        self.assertIn("where python", content)
        self.assertIn(r'findstr /I /C:"WindowsApps\python.exe"', content)
        self.assertIn("-m harbor.bridges.wechat_bridge", content)


if __name__ == "__main__":
    unittest.main()
