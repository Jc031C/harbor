from harbor.core.config import HarborConfig


class PermissionService:
    def __init__(self, config: HarborConfig):
        self.config = config

    def is_allowed(self, sender: str) -> bool:
        whitelist = self.config.permission_whitelist

        if not whitelist:
            return False

        return sender in whitelist

    def deny_message(self, sender: str) -> str:
        return f"权限拒绝：用户 {sender} 不在 Harbor v0.1 白名单中。"
