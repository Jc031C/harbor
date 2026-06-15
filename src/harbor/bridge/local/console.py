from typing import Optional

from harbor.core.models import HarborRequest


class LocalConsoleBridge:
    def __init__(self, sender: str = "developer"):
        self.sender = sender
        self.started = False

    def receive(self) -> Optional[HarborRequest]:
        if not self.started:
            self._print_start_message()
            self.started = True

        try:
            text = input("你 > ")
        except (EOFError, KeyboardInterrupt):
            print("")
            return None

        cleaned_text = text.strip()

        if cleaned_text.lower() in ["exit", "quit", "q"] or cleaned_text == "退出":
            return None

        return HarborRequest(
            source="local-console",
            sender=self.sender,
            text=cleaned_text,
        )

    def _print_start_message(self) -> None:
        print("Harbor Local Bridge 已启动。")
        print("输入 帮助 查看指令。")
        print("输入 exit、quit、q 或 退出 可以关闭。")
        print("")
