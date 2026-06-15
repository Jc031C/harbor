from harbor.core.config import HarborConfig
from harbor.core.task import Task
from harbor.workers.gpt_desktop_worker import GPTDesktopWorker
from harbor.workers.mock_worker import MockWorker
from harbor.workers.system_worker import SystemWorker


class Router:
    def __init__(self, config: HarborConfig):
        self.config = config
        self.mock_worker = MockWorker()
        self.system_worker = SystemWorker(config)
        self.gpt_desktop_worker = GPTDesktopWorker(config)

    def route(self, task: Task):
        if task.command == "/mock":
            return self.mock_worker

        if task.command == "/gpt":
            return self.gpt_desktop_worker

        if task.command in ["/help", "/status"]:
            return self.system_worker

        return self.system_worker
