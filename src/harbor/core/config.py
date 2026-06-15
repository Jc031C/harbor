import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class HarborConfig:
    settings: dict[str, Any]

    @property
    def app_name(self) -> str:
        return self.settings.get("app", {}).get("name", "Harbor")

    @property
    def version(self) -> str:
        return self.settings.get("app", {}).get("version", "0.1.1")

    @property
    def debug(self) -> bool:
        return bool(self.settings.get("app", {}).get("debug", False))

    @property
    def default_bridge(self) -> str:
        return self.settings.get("bridge", {}).get("default", "mock")

    @property
    def enabled_workers(self) -> list[str]:
        return list(self.settings.get("workers", {}).get("enabled", []))

    @property
    def permission_whitelist(self) -> list[str]:
        return list(self.settings.get("permission", {}).get("whitelist", []))

    @property
    def gpt_desktop_enabled(self) -> bool:
        return bool(self.settings.get("gpt_desktop", {}).get("enabled", False))

    @property
    def log_path(self) -> str:
        return self.settings.get("logs", {}).get("path", "data/logs/harbor.log")


def load_config(path: str | Path = "config/settings.json") -> HarborConfig:
    config_path = Path(path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        settings = json.load(file)

    return HarborConfig(settings=settings)
