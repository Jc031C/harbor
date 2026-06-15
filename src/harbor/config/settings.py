import os
from dataclasses import dataclass


@dataclass(frozen=True)
class HarborSettings:
    env: str = "development"
    app_name: str = "Harbor"
    version: str = "0.1.0"


def load_settings() -> HarborSettings:
    return HarborSettings(
        env=os.getenv("HARBOR_ENV", "development"),
        app_name=os.getenv("HARBOR_APP_NAME", "Harbor"),
        version=os.getenv("HARBOR_VERSION", "0.1.0"),
    )
