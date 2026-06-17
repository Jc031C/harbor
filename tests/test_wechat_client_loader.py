import unittest
from types import SimpleNamespace
from unittest.mock import patch

from harbor.bridges.wechat_client_loader import WeChatClientLoadError, load_wechat_client


class Wxauto4WeChat:
    pass


class WxautoWeChat:
    pass


class TestWeChatClientLoader(unittest.TestCase):
    def test_prefers_wxauto4_when_available(self):
        imported_modules = []

        def fake_import(module_name):
            imported_modules.append(module_name)
            if module_name == "wxauto4":
                return SimpleNamespace(WeChat=Wxauto4WeChat)
            if module_name == "wxauto":
                return SimpleNamespace(WeChat=WxautoWeChat)
            raise ImportError(module_name)

        with patch("harbor.bridges.wechat_client_loader.import_module", side_effect=fake_import):
            wechat_class = load_wechat_client()

        self.assertIs(wechat_class, Wxauto4WeChat)
        self.assertEqual(imported_modules, ["wxauto4"])

    def test_falls_back_to_wxauto_when_wxauto4_is_missing(self):
        imported_modules = []

        def fake_import(module_name):
            imported_modules.append(module_name)
            if module_name == "wxauto4":
                raise ImportError("No module named 'wxauto4'")
            if module_name == "wxauto":
                return SimpleNamespace(WeChat=WxautoWeChat)
            raise ImportError(module_name)

        with patch("harbor.bridges.wechat_client_loader.import_module", side_effect=fake_import):
            wechat_class = load_wechat_client()

        self.assertIs(wechat_class, WxautoWeChat)
        self.assertEqual(imported_modules, ["wxauto4", "wxauto"])

    def test_raises_clear_error_when_no_supported_library_exists(self):
        def fake_import(module_name):
            raise ImportError(f"No module named '{module_name}'")

        with patch("harbor.bridges.wechat_client_loader.import_module", side_effect=fake_import):
            with self.assertRaises(WeChatClientLoadError) as context:
                load_wechat_client()

        message = str(context.exception)
        self.assertIn("wxauto4", message)
        self.assertIn("wxauto", message)
        self.assertIn("WeChat 4.x", message)

    def test_raises_clear_error_when_wechat_class_is_missing(self):
        def fake_import(module_name):
            return SimpleNamespace()

        with patch("harbor.bridges.wechat_client_loader.import_module", side_effect=fake_import):
            with self.assertRaises(WeChatClientLoadError) as context:
                load_wechat_client()

        self.assertIn("missing WeChat class", str(context.exception))


if __name__ == "__main__":
    unittest.main()
