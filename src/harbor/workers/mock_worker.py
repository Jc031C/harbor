from harbor.core.task import Task, WorkerResult


class MockWorker:
    name = "mock_worker"

    def handle(self, task: Task) -> WorkerResult:
        content = task.content.strip()

        if not content:
            content = "empty mock content"

        return WorkerResult(
            success=True,
            message=f"Mock Worker 已收到：{content}",
            worker_name=self.name,
        )
