from importlib import import_module
from typing import Any


class WeChatClientLoadError(RuntimeError):
    """Raised when no supported WeChat automation package can be loaded."""


def load_wechat_client() -> type[Any]:
    """Load the preferred WeChat automation client class.

    wxauto4 supports the current Windows WeChat 4.x line. wxauto remains as a
    compatibility fallback for older local environments.
    """

    errors: list[str] = []

    for module_name in ["wxauto4", "wxauto"]:
        try:
            module = import_module(module_name)
        except ImportError as exc:
            errors.append(f"{module_name}: {exc}")
            continue

        wechat_class = getattr(module, "WeChat", None)
        if wechat_class is None:
            errors.append(f"{module_name}: missing WeChat class")
            continue

        return wechat_class

    details = "; ".join(errors) if errors else "no import attempts were made"
    raise WeChatClientLoadError(
        "No supported WeChat automation library is available. "
        "Tried wxauto4 first, then wxauto. "
        "For WeChat 4.x, install wxauto4 in the active Python environment. "
        f"Details: {details}"
    )
