from harbor.connectors.llm.mock_llm import MockLLMConnector
from harbor.core.models import HarborRequest, HarborResponse
from harbor.core.router import CommandRouter


class HarborCore:
    def __init__(self):
        self.router = CommandRouter()
        self.llm = MockLLMConnector()

    def handle(self, request: HarborRequest) -> HarborResponse:
        text = request.text.strip()

        routed_response = self.router.route(text)
        if routed_response is not None:
            return routed_response

        normalized_text = text.lower()

        if text.startswith("问 "):
            question = text[2:].strip()
            return self._handle_llm_question(question)

        if normalized_text.startswith("ask "):
            question = text[4:].strip()
            return self._handle_llm_question(question)

        return HarborResponse(
            text=(
                f"Harbor 已收到你的消息：{text}\n"
                "当前 v0.1 只负责本地链路验证。后续会逐步接入微信、GPT 和家庭服务器工具。"
            )
        )

    def _handle_llm_question(self, question: str) -> HarborResponse:
        if not question:
            return HarborResponse(
                text="你想问什么？请使用：问 你的问题",
                success=False,
            )

        answer = self.llm.ask(question)

        return HarborResponse(
            text=answer,
            handled_by="mock-llm-connector",
        )
