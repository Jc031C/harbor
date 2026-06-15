class MockLLMConnector:
    def ask(self, prompt: str) -> str:
        return (
            "我现在还没有接入真实大模型。\n"
            f"v0.1 已收到你的问题：{prompt}\n"
            "后续 v0.3 会把这里替换成 GPT Desktop Connector 或其他 LLM Connector。"
        )
