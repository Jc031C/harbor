from dataclasses import replace

from harbor.bridges.base_bridge import BridgeInput
from harbor.bridges.local_queue_bridge import LocalQueueBridge
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
            metadata=dict(bridge_input.metadata),
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
        metadata=dict(bridge_input.metadata),
    )

    logger.info(
        "Built task sender=%s command=%s content=%s",
        task.sender,
        task.command,
        task.content,
    )

    worker = router.route(task)
    result = worker.handle(task)

    if task.metadata:
        merged_metadata = dict(task.metadata)
        merged_metadata.update(result.metadata)
        result = replace(result, metadata=merged_metadata)

    logger.info(
        "Worker result worker=%s success=%s message=%s",
        result.worker_name,
        result.success,
        result.message,
    )

    return result


def run_mock_bridge(
    router: Router,
    permission_service: PermissionService,
    logger,
) -> None:
    bridge = MockBridge()

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


def run_local_queue_bridge(
    config,
    router: Router,
    permission_service: PermissionService,
    logger,
) -> None:
    bridge = LocalQueueBridge.from_config(config)

    processed_count = bridge.process_all(
        handler=lambda bridge_input: handle_bridge_input(
            bridge_input=bridge_input,
            router=router,
            permission_service=permission_service,
            logger=logger,
        )
    )

    print(f"Local Queue Bridge 处理完成：{processed_count} 个文件。")


def main():
    config = load_config()
    logger = get_logger("harbor", config.log_path)
    permission_service = PermissionService(config)
    router = Router(config)

    logger.info(
        "Starting %s version=%s default_bridge=%s",
        config.app_name,
        config.version,
        config.default_bridge,
    )

    if config.default_bridge == "local_queue":
        run_local_queue_bridge(
            config=config,
            router=router,
            permission_service=permission_service,
            logger=logger,
        )
    elif config.default_bridge == "mock":
        run_mock_bridge(
            router=router,
            permission_service=permission_service,
            logger=logger,
        )
    else:
        raise ValueError(f"Unsupported bridge.default: {config.default_bridge}")

    logger.info("Harbor stopped.")
    print("Harbor 已退出。")


if __name__ == "__main__":
    main()
