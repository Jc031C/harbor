from harbor.core.config import HarborConfig
from harbor.core.task import Task, WorkerResult


class GPTDesktopWorker:
    name = "gpt_desktop_worker"

    def __init__(self, config: HarborConfig):
        self.config = config

    def handle(self, task: Task) -> WorkerResult:
        content = task.content.strip()

        if not content:
            return WorkerResult(
                success=False,
                message="请在 /gpt 后输入要测试的内容。",
                worker_name=self.name,
            )

        if not self.config.gpt_desktop_enabled:
            return WorkerResult(
                success=True,
                message=(
                    "GPT Desktop Worker 当前是 v0.1 占位回复。\n"
                    "真实 ChatGPT 桌面端接入尚未启用。\n"
                    f"已收到测试内容：{content}"
                ),
                worker_name=self.name,
            )

        return WorkerResult(
            success=True,
            message=(
                "GPT Desktop Worker 配置已启用，但 v0.1 不执行真实桌面端调用。\n"
                f"已收到测试内容：{content}"
            ),
            worker_name=self.name,
        )
