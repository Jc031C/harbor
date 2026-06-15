from harbor.bridge.local.console import LocalConsoleBridge
from harbor.config.settings import load_settings
from harbor.core.engine import HarborCore
from harbor.core.main_loop import HarborMainLoop
from harbor.return_channels.local.console import LocalConsoleReturnChannel
from harbor.utils.logger import get_logger


def main():
    settings = load_settings()
    logger = get_logger("harbor")

    logger.info(
        "Starting %s version=%s env=%s",
        settings.app_name,
        settings.version,
        settings.env,
    )

    bridge = LocalConsoleBridge()
    return_channel = LocalConsoleReturnChannel()
    core = HarborCore()

    loop = HarborMainLoop(
        bridge=bridge,
        return_channel=return_channel,
        core=core,
        logger=logger,
    )

    loop.run_forever()


if __name__ == "__main__":
    main()
