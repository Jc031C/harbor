from harbor.bridges.base_bridge import BridgeInput
from harbor.bridges.mock_bridge import MockBridge
from harbor.core.config import load_config
from harbor.core.router import Router
from harbor.core.task import WorkerResult, build_task
from harbor.services.logger_service import get_logger
from harbor.services.permission_service import PermissionService


def handle_bridge_input(
    bridge_input: BridgeInput,
    router: Router,
    permission_service: PermissionService,
    logger,
) -> WorkerResult:
    logger.info(
        "Received bridge input source=%s sender=%s raw_text=%s",
        bridge_input.source,
        bridge_input.sender,
        bridge_input.raw_text,
    )

    if not permission_service.is_allowed(bridge_input.sender):
        result = WorkerResult(
            success=False,
            message=permission_service.deny_message(bridge_input.sender),
            worker_name="permission_service",
        )

        logger.warning(
            "Permission denied sender=%s source=%s",
            bridge_input.sender,
            bridge_input.source,
        )

        return result

    task = build_task(
        source=bridge_input.source,
        sender=bridge_input.sender,
        raw_text=bridge_input.raw_text,
    )

    logger.info(
        "Built task sender=%s command=%s content=%s",
        task.sender,
        task.command,
        task.content,
    )

    worker = router.route(task)
    result = worker.handle(task)

    logger.info(
        "Worker result worker=%s success=%s message=%s",
        result.worker_name,
        result.success,
        result.message,
    )

    return result


def main():
    config = load_config()
    logger = get_logger("harbor", config.log_path)
    permission_service = PermissionService(config)
    router = Router(config)
    bridge = MockBridge()

    logger.info(
        "Starting %s version=%s default_bridge=%s",
        config.app_name,
        config.version,
        config.default_bridge,
    )

    try:
        while True:
            bridge_input = bridge.receive()

            if bridge_input is None:
                break

            result = handle_bridge_input(
                bridge_input=bridge_input,
                router=router,
                permission_service=permission_service,
                logger=logger,
            )

            bridge.send_result(result)
    except KeyboardInterrupt:
        print("")
    finally:
        logger.info("Harbor stopped.")
        print("Harbor 已退出。")


if __name__ == "__main__":
    main()
