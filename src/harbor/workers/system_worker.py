from harbor.core.config import HarborConfig
from harbor.core.task import Task, WorkerResult


class SystemWorker:
    name = "system_worker"

    def __init__(self, config: HarborConfig):
        self.config = config

    def handle(self, task: Task) -> WorkerResult:
        if task.command == "/help":
            return self._help()

        if task.command == "/status":
            return self._status()

        return self._unknown(task)

    def _help(self) -> WorkerResult:
        return WorkerResult(
            success=True,
            message=(
                "Harbor 可用命令：\n"
                "/mock 内容：使用 Mock Worker 测试任务链路\n"
                "/gpt 内容：调用 GPT Desktop Worker 占位回复\n"
                "/help：查看帮助\n"
                "/status：查看运行状态"
            ),
            worker_name=self.name,
        )

    def _status(self) -> WorkerResult:
        return WorkerResult(
            success=True,
            message=(
                "Harbor 状态：运行中\n"
                f"应用名称：{self.config.app_name}\n"
                f"版本：{self.config.version}\n"
                f"Debug：{self.config.debug}\n"
                f"默认 Bridge：{self.config.default_bridge}\n"
                f"启用 Workers：{', '.join(self.config.enabled_workers)}"
            ),
            worker_name=self.name,
        )

    def _unknown(self, task: Task) -> WorkerResult:
        return WorkerResult(
            success=False,
            message=(
                f"未知命令：{task.command}\n"
                "请使用 /help 查看 Harbor 支持的命令。"
            ),
            worker_name=self.name,
        )
