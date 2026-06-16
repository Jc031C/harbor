from typing import Optional

from harbor.bridges.base_bridge import BridgeInput
from harbor.core.task import WorkerResult


class MockBridge:
    name = "mock_bridge"

    def __init__(self, sender: str = "developer"):
        self.sender = sender
        self.started = False

    def receive(self) -> Optional[BridgeInput]:
        if not self.started:
            self._print_start_message()
            self.started = True

        try:
            raw_text = input("你 > ")
        except (EOFError, KeyboardInterrupt):
            print("")
            return None

        cleaned_text = raw_text.strip()

        if cleaned_text.lower() in ["exit", "quit", "q"] or cleaned_text == "退出":
            return None

        return BridgeInput(
            source=self.name,
            sender=self.sender,
            raw_text=cleaned_text,
        )

    def send_result(self, result: WorkerResult) -> None:
        print(f"Harbor > {result.message}")
        print("")

    def _print_start_message(self) -> None:
        print("Harbor Mock Bridge 已启动。")
        print("当前支持命令：/mock、/gpt、/help、/status")
        print("输入 exit、quit、q 或 退出 可以关闭。")
        print("")
