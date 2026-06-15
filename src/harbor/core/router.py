from typing import Optional

from harbor.core.models import HarborResponse


class CommandRouter:
    def route(self, text: str) -> Optional[HarborResponse]:
        cleaned_text = text.strip()

        if not cleaned_text:
            return HarborResponse(
                text="我收到了一条空消息，请重新发送。",
                success=False,
            )

        normalized_text = cleaned_text.lower()

        if cleaned_text in ["你好", "您好"] or normalized_text in ["hello", "hi"]:
            return HarborResponse(
                text="你好，我是 Harbor Core。当前核心中枢已启动。"
            )

        if cleaned_text in ["帮助", "菜单"] or normalized_text in ["help", "/help"]:
            return HarborResponse(
                text=(
                    "Harbor 当前可用指令：\n"
                    "1. 你好：测试 Harbor Core 是否启动\n"
                    "2. 状态：查看 Harbor 当前运行状态\n"
                    "3. 帮助：查看当前可用指令\n"
                    "4. 问 你的问题：模拟转交给大模型连接器\n"
                    "5. exit：退出本地运行"
                )
            )

        if cleaned_text in ["状态", "运行状态"] or normalized_text in ["status", "/status"]:
            return HarborResponse(
                text=(
                    "Harbor 状态：运行中\n"
                    "当前版本：v0.1.0\n"
                    "当前阶段：本地初始化验证\n"
                    "真实微信接入：未启用\n"
                    "真实 GPT 接入：未启用"
                )
            )

        return None
