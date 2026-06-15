class GPTDesktopConnectorPlaceholder:
    def ask(self, prompt: str) -> str:
        return (
            "GPT Desktop Connector 目前只是占位模块。\n"
            f"收到的问题：{prompt}\n"
            "真实桌面端 GPT 调用会在后续版本实现。"
        )
