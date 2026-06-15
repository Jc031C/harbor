from typing import Optional

from harbor.bridges.base_bridge import BridgeInput
from harbor.core.task import WorkerResult


class WechatBridge:
    name = "wechat_bridge"

    def receive(self) -> Optional[BridgeInput]:
        return None

    def send_result(self, result: WorkerResult) -> None:
        raise NotImplementedError(
            "WechatBridge 是 v0.1 占位模块，当前不接入真实微信。"
        )
