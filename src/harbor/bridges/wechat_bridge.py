import json
import shutil
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Protocol
from uuid import uuid4

from harbor.bridges.wechat_client_loader import WeChatClientLoadError, load_wechat_client
from harbor.core.config import HarborConfig, load_config


@dataclass(frozen=True)
class WeChatIncomingMessage:
    """A normalized incoming WeChat message used by the queue adapter."""

    sender_name: str
    content: str
    sender_id: str = ""


@dataclass(frozen=True)
class WeChatReply:
    """A normalized Harbor outbox result waiting to be sent to WeChat."""

    path: Path
    receiver_name: str
    receiver_id: str
    content: str
    payload: dict[str, Any]


class WeChatClient(Protocol):
    """Small protocol used to keep tests independent from a real WeChat client."""

    def get_messages(self) -> list[WeChatIncomingMessage]:
        ...

    def send_message(self, contact_name: str, content: str) -> None:
        ...


class WeChatUnavailableError(RuntimeError):
    """Raised when the optional real WeChat automation layer is unavailable."""


class WxAutoWeChatClient:
    """Optional wxauto-backed client.

    This wrapper is deliberately isolated from Harbor Core. Unit tests should pass
    a fake client instead of using wxauto or a real Windows WeChat session.
    """

    def __init__(self, target_contact_name: str, enable_listener: bool = False):
        if not target_contact_name:
            raise WeChatUnavailableError(
                "wechat.target_contact_name 为空。请先在 config/settings.json 中填写测试联系人。"
            )

        try:
            WeChat = load_wechat_client()
        except WeChatClientLoadError as exc:
            raise WeChatUnavailableError(
                f"{exc}"
            ) from exc

        try:
            self.wx = WeChat(ads=False, resize=False)
        except Exception as exc:  # noqa: BLE001 - external UI automation can fail broadly.
            raise WeChatUnavailableError(
                "无法连接 Windows 微信客户端。请确认微信已打开、已登录，并且窗口未被系统阻止。"
            ) from exc

        self.target_contact_name = target_contact_name
        self._buffer: list[WeChatIncomingMessage] = []
        self._seen_message_keys: set[str] = set()
        self._poll_initialized = False
        self._listening = False

        if enable_listener:
            self._try_enable_listener()

    def get_messages(self) -> list[WeChatIncomingMessage]:
        if self._listening:
            messages = list(self._buffer)
            self._buffer.clear()
            return messages

        return self._poll_messages()

    def send_message(self, contact_name: str, content: str) -> None:
        try:
            chat_with = getattr(self.wx, "ChatWith", None)
            if not callable(chat_with):
                raise WeChatUnavailableError("当前 wxauto 版本不支持 ChatWith，无法切换微信联系人。")

            chat_info = getattr(self.wx, "ChatInfo", None)
            if not callable(chat_info):
                raise WeChatUnavailableError("当前 wxauto 版本不支持 ChatInfo，无法校验微信联系人。")

            send_msg = getattr(self.wx, "SendMsg", None)
            if not callable(send_msg):
                raise WeChatUnavailableError("当前 wxauto 版本不支持 SendMsg，无法发送微信消息。")

            chat_with(contact_name, exact=True)
            info = chat_info()

            if not isinstance(info, dict) or info.get("chat_name") != contact_name:
                raise WeChatUnavailableError(
                    f"微信目标联系人校验失败：expected={contact_name} actual={info}"
                )

            send_msg(content)
        except WeChatUnavailableError:
            raise
        except Exception as exc:  # noqa: BLE001 - external UI automation can fail broadly.
            raise WeChatUnavailableError(f"发送微信消息失败：{exc}") from exc

    def stop(self) -> None:
        stop_listening = getattr(self.wx, "StopListening", None)
        if callable(stop_listening):
            stop_listening()

    def _try_enable_listener(self) -> None:
        add_listen_chat = getattr(self.wx, "AddListenChat", None)
        if not callable(add_listen_chat):
            return

        try:
            add_listen_chat(self.target_contact_name, self._on_message)
            self._listening = True
        except Exception:
            self._listening = False

    def _on_message(self, msg: Any, chat: Any) -> None:
        content = self._extract_message_content(msg)
        if not content:
            return

        sender_name = self._extract_sender_name(msg, chat) or self.target_contact_name
        self._buffer.append(
            WeChatIncomingMessage(
                sender_name=sender_name,
                sender_id=f"wechat_{sender_name}",
                content=content,
            )
        )

    def _poll_messages(self) -> list[WeChatIncomingMessage]:
        try:
            chat_with = getattr(self.wx, "ChatWith", None)
            if callable(chat_with):
                chat_with(self.target_contact_name)

            chat_info = getattr(self.wx, "ChatInfo", None)
            if callable(chat_info):
                info = chat_info()
                if isinstance(info, dict) and info.get("chat_name") != self.target_contact_name:
                    raise WeChatUnavailableError(
                        f"微信目标联系人校验失败：expected={self.target_contact_name} actual={info}"
                    )

            get_all_message = getattr(self.wx, "GetAllMessage", None)
            if not callable(get_all_message):
                raise WeChatUnavailableError(
                    "当前 wxauto 版本不支持 GetAllMessage，无法轮询微信消息。"
                )

            raw_messages = get_all_message()
        except WeChatUnavailableError:
            raise
        except Exception as exc:  # noqa: BLE001 - external UI automation can fail broadly.
            raise WeChatUnavailableError(f"读取微信消息失败：{exc}") from exc

        normalized_messages: list[WeChatIncomingMessage] = []
        current_keys: set[str] = set()

        for raw_message in raw_messages or []:
            content = self._extract_message_content(raw_message)
            if not content:
                continue

            sender_name = self._extract_sender_name(raw_message, None) or self.target_contact_name
            message_key = self._message_key(sender_name, content, raw_message)
            current_keys.add(message_key)

            if self._poll_initialized and message_key not in self._seen_message_keys:
                normalized_messages.append(
                    WeChatIncomingMessage(
                        sender_name=sender_name,
                        sender_id=f"wechat_{sender_name}",
                        content=content,
                    )
                )

        self._seen_message_keys.update(current_keys)
        self._poll_initialized = True
        return normalized_messages

    def _extract_message_content(self, raw_message: Any) -> str:
        for attr_name in ["content", "text", "message", "msg"]:
            value = getattr(raw_message, attr_name, None)
            if isinstance(value, str) and value.strip():
                return value.strip()

        if isinstance(raw_message, str) and raw_message.strip():
            return raw_message.strip()

        return ""

    def _extract_sender_name(self, raw_message: Any, chat: Any) -> str:
        for source in [raw_message, chat]:
            for attr_name in ["sender", "sender_name", "nickname", "who", "name"]:
                value = getattr(source, attr_name, None)
                if isinstance(value, str) and value.strip():
                    return value.strip()

        if isinstance(chat, str) and chat.strip():
            return chat.strip()

        return ""

    def _message_key(self, sender_name: str, content: str, raw_message: Any) -> str:
        time_value = ""
        for attr_name in ["time", "create_time", "created_at"]:
            value = getattr(raw_message, attr_name, None)
            if value:
                time_value = str(value)
                break

        return f"{sender_name}|{time_value}|{content}"


class WeChatQueueAdapter:
    """Adapter between Windows WeChat automation and Harbor local queue files.

    It only translates messages between WeChat and data/inbox + data/outbox.
    It does not parse commands, route tasks, call GPT, or bypass Permission.
    """

    name = "wechat_queue_adapter"

    def __init__(
        self,
        inbox_path: str | Path = "data/inbox",
        outbox_path: str | Path = "data/outbox",
        sent_path: str | Path = "data/wechat/sent",
        failed_path: str | Path = "data/wechat/failed",
        logs_path: str | Path = "data/wechat/logs",
        allowed_senders: list[str] | None = None,
        target_contact_name: str = "",
        poll_interval_seconds: int = 2,
        reply_check_interval_seconds: int = 2,
        auto_reply: bool = True,
        enabled: bool = False,
        mode: str = "send_only",
    ):
        self.inbox_path = Path(inbox_path)
        self.outbox_path = Path(outbox_path)
        self.sent_path = Path(sent_path)
        self.failed_path = Path(failed_path)
        self.logs_path = Path(logs_path)
        self.allowed_senders = set(allowed_senders or [])
        self.target_contact_name = target_contact_name
        self.poll_interval_seconds = max(1, int(poll_interval_seconds))
        self.reply_check_interval_seconds = max(1, int(reply_check_interval_seconds))
        self.auto_reply = bool(auto_reply)
        self.enabled = bool(enabled)
        self.mode = mode.strip() or "send_only"
        self.log_file_path = self.logs_path / "wechat_bridge.log"
        self.listen_state_path = self.logs_path.parent / "listen_state.json"
        self._ensure_directories()

    @classmethod
    def from_config(cls, config: HarborConfig) -> "WeChatQueueAdapter":
        return cls(
            inbox_path=config.local_queue_inbox_path,
            outbox_path=config.local_queue_outbox_path,
            sent_path=config.wechat_sent_path,
            failed_path=config.wechat_failed_path,
            logs_path=config.wechat_logs_path,
            allowed_senders=config.wechat_allowed_senders,
            target_contact_name=config.wechat_target_contact_name,
            poll_interval_seconds=config.wechat_poll_interval_seconds,
            reply_check_interval_seconds=config.wechat_reply_check_interval_seconds,
            auto_reply=config.wechat_auto_reply,
            enabled=config.wechat_enabled,
            mode=config.wechat_mode,
        )

    def process_incoming_once(self, wechat_client: WeChatClient | None) -> int:
        """Read one batch of WeChat messages and write allowed messages to inbox."""
        if wechat_client is None:
            self._append_log("微信客户端不可用，跳过本轮消息读取。")
            return 0

        written_count = 0

        try:
            messages = wechat_client.get_messages()
        except Exception as exc:  # noqa: BLE001 - external UI automation can fail broadly.
            self._append_log(f"读取微信消息失败：{exc}")
            return 0

        for message in messages:
            output_path = self.write_incoming_message(
                sender_name=message.sender_name,
                message=message.content,
                sender_id=message.sender_id,
            )
            if output_path is not None:
                written_count += 1

        return written_count

    def process_listen_once(self, wechat_client: WeChatClient | None) -> int:
        """Read one batch of WeChat messages, dedupe it, and write allowed text to inbox."""
        if wechat_client is None:
            self._append_log("微信客户端不可用，跳过 listen 消息读取。")
            return 0

        try:
            messages = wechat_client.get_messages()
        except Exception as exc:  # noqa: BLE001 - external UI automation can fail broadly.
            self._append_log(f"listen 读取微信消息失败：{exc}")
            return 0

        listen_state = self._load_listen_state()
        last_fingerprint = str(listen_state.get("last_fingerprint") or "")
        written_count = 0

        for message in messages:
            if not self._is_allowed_incoming_message(message):
                continue

            fingerprint = self._fingerprint_incoming_message(message)
            if fingerprint == last_fingerprint:
                continue

            output_path = self._write_incoming_task(message)
            if output_path is None:
                continue

            last_fingerprint = fingerprint
            listen_state["last_fingerprint"] = fingerprint
            self._save_listen_state(listen_state)
            written_count += 1

        return written_count

    def write_incoming_message(
        self,
        sender_name: str,
        message: str,
        sender_id: str = "",
    ) -> Path | None:
        """Write one allowed WeChat message into Harbor's local inbox."""
        sender_name = sender_name.strip()
        message = message.strip()

        if not sender_name or not message:
            self._append_log("收到空 sender 或空 message，已忽略。")
            return None

        if not self.is_allowed_sender(sender_name):
            self._append_log(f"忽略非白名单联系人消息：{sender_name}")
            return None

        if self.target_contact_name and sender_name != self.target_contact_name:
            self._append_log(
                f"忽略非目标联系人消息：sender={sender_name} target={self.target_contact_name}"
            )
            return None

        payload = {
            "source": "wechat",
            "sender_id": sender_id.strip() or f"wechat_{sender_name}",
            "sender_name": sender_name,
            "message": message,
            "created_at": self._now_text(),
        }

        output_path = self._unique_path(
            self.inbox_path / f"wechat_{self._timestamp_for_filename()}_{uuid4().hex[:8]}.json"
        )

        with output_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
            file.write("\n")

        self._append_log(f"写入微信消息到 inbox：{output_path.name}")
        return output_path

    def collect_pending_replies(self) -> list[WeChatReply]:
        """Collect pending outbox result files that should be sent to WeChat."""
        replies: list[WeChatReply] = []

        for result_path in sorted(self.outbox_path.glob("*.json")):
            if not result_path.is_file():
                continue

            payload = self._read_json_or_quarantine(result_path)
            if payload is None:
                continue

            reply = self._payload_to_reply(result_path, payload)
            if reply is not None:
                replies.append(reply)

        return replies

    def process_outbox_once(self, wechat_client: WeChatClient | None) -> int:
        """Send one batch of Harbor outbox results back to WeChat."""
        replies = self.collect_pending_replies()
        return self.process_outbox_replies_once(wechat_client, replies)

    def process_outbox_replies_once(
        self,
        wechat_client: WeChatClient | None,
        replies: list[WeChatReply],
    ) -> int:
        """Send a pre-collected batch of Harbor outbox results back to WeChat."""
        sent_count = 0

        if not self.auto_reply:
            self._append_log("wechat.auto_reply=false，跳过自动回复。")
            return 0

        for reply in replies:
            if wechat_client is None:
                self._append_log(f"微信客户端不可用，无法发送：{reply.path.name}")
                self._move_file(reply.path, self.failed_path)
                continue

            try:
                wechat_client.send_message(reply.receiver_name, reply.content)
            except Exception as exc:  # noqa: BLE001 - external UI automation can fail broadly.
                self._append_log(f"发送微信回复失败：{reply.path.name}，原因：{exc}")
                self._move_file(reply.path, self.failed_path)
                continue

            self._append_log(f"发送微信回复成功：{reply.path.name} -> {reply.receiver_name}")
            self._move_file(reply.path, self.sent_path)
            sent_count += 1

        return sent_count

    def process_send_only_once(self, client_factory: Callable[[], WeChatClient]) -> int:
        """Process pending replies without initializing WeChat when there is nothing to send."""
        if not self.auto_reply:
            self._append_log("wechat.auto_reply=false，跳过自动回复。")
            return 0

        replies = self.collect_pending_replies()
        if not replies:
            return 0

        try:
            wechat_client = client_factory()
        except Exception as exc:  # noqa: BLE001 - external UI automation can fail broadly.
            self._append_log(f"初始化微信客户端失败：{exc}")
            return self.process_outbox_replies_once(None, replies)

        try:
            return self.process_outbox_replies_once(wechat_client, replies)
        finally:
            stop = getattr(wechat_client, "stop", None)
            if callable(stop):
                stop()

    def run_forever(self, wechat_client: WeChatClient) -> None:
        """Run the adapter as a small standalone bridge process."""
        self._append_log("WeChat Queue Adapter 已启动。")

        try:
            while True:
                self.process_incoming_once(wechat_client)
                self.process_outbox_once(wechat_client)
                time.sleep(min(self.poll_interval_seconds, self.reply_check_interval_seconds))
        except KeyboardInterrupt:
            self._append_log("WeChat Queue Adapter 收到停止信号。")
        finally:
            stop = getattr(wechat_client, "stop", None)
            if callable(stop):
                stop()

    def run_send_only_forever(self, client_factory: Callable[[], WeChatClient]) -> None:
        """Run the adapter in send-only mode with lazy WeChat client creation."""
        self._append_log("WeChat Queue Adapter 已启动：send_only。")

        try:
            while True:
                self.process_send_only_once(client_factory)
                time.sleep(self.reply_check_interval_seconds)
        except KeyboardInterrupt:
            self._append_log("WeChat Queue Adapter 收到停止信号。")

    def run_listen_forever(self, wechat_client: WeChatClient) -> None:
        """Run the adapter in listen mode without sending WeChat replies."""
        self._append_log("WeChat Queue Adapter 已启动：listen。")

        try:
            while True:
                self.process_listen_once(wechat_client)
                time.sleep(self.poll_interval_seconds)
        except KeyboardInterrupt:
            self._append_log("WeChat Queue Adapter 收到停止信号。")
        finally:
            stop = getattr(wechat_client, "stop", None)
            if callable(stop):
                stop()

    def is_allowed_sender(self, sender_name: str) -> bool:
        return sender_name in self.allowed_senders

    def _is_allowed_incoming_message(self, message: WeChatIncomingMessage) -> bool:
        sender_name = str(getattr(message, "sender_name", "") or "").strip()
        content = getattr(message, "content", "")

        if not sender_name or not isinstance(content, str) or not content.strip():
            self._append_log("listen 收到非文本消息或空消息，已忽略。")
            return False

        if not self.allowed_senders:
            self._append_log("wechat.allowed_senders 为空，listen 默认拒绝写入 inbox。")
            return False

        if not self.is_allowed_sender(sender_name):
            self._append_log(f"listen 忽略非白名单联系人消息：{sender_name}")
            return False

        if self.target_contact_name and sender_name != self.target_contact_name:
            self._append_log(
                f"listen 忽略非目标联系人消息：sender={sender_name} target={self.target_contact_name}"
            )
            return False

        return True

    def _write_incoming_task(self, message: WeChatIncomingMessage) -> Path | None:
        return self.write_incoming_message(
            sender_name=message.sender_name,
            message=message.content,
            sender_id=message.sender_id,
        )

    def _fingerprint_incoming_message(self, message: WeChatIncomingMessage) -> str:
        return "|".join(
            [
                str(getattr(message, "sender_name", "") or "").strip(),
                str(getattr(message, "sender_id", "") or "").strip(),
                str(getattr(message, "content", "") or "").strip(),
            ]
        )

    def _load_listen_state(self) -> dict[str, Any]:
        if not self.listen_state_path.exists():
            return {}

        try:
            with self.listen_state_path.open("r", encoding="utf-8") as file:
                state = json.load(file)
        except Exception as exc:  # noqa: BLE001 - bad local state should not stop listen mode.
            self._append_log(f"读取 listen_state 失败，已重置：{exc}")
            return {}

        return state if isinstance(state, dict) else {}

    def _save_listen_state(self, state: dict[str, Any]) -> None:
        self.listen_state_path.parent.mkdir(parents=True, exist_ok=True)
        with self.listen_state_path.open("w", encoding="utf-8") as file:
            json.dump(state, file, ensure_ascii=False, indent=2)
            file.write("\n")

    def _payload_to_reply(
        self,
        result_path: Path,
        payload: dict[str, Any],
    ) -> WeChatReply | None:
        if "source" in payload:
            source = str(payload.get("source") or "").strip()
            if source != "wechat":
                return None

        receiver_name = str(payload.get("receiver_name") or "").strip()
        receiver_id = str(payload.get("receiver_id") or "").strip()
        content = str(payload.get("content") or "").strip()

        if not receiver_name or not content:
            self._append_log(f"outbox 结果缺少 receiver_name 或 content，移入 failed：{result_path.name}")
            self._move_file(result_path, self.failed_path)
            return None

        if self.target_contact_name and receiver_name != self.target_contact_name:
            return None

        if not self.is_allowed_sender(receiver_name):
            return None

        if "source" not in payload and not receiver_id.startswith("wechat_"):
            return None

        if receiver_id and not receiver_id.startswith("wechat_"):
            return None

        return WeChatReply(
            path=result_path,
            receiver_name=receiver_name,
            receiver_id=receiver_id,
            content=content,
            payload=payload,
        )

    def _read_json_or_quarantine(self, result_path: Path) -> dict[str, Any] | None:
        try:
            with result_path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except Exception as exc:  # noqa: BLE001 - bridge must quarantine bad files.
            self._append_log(f"读取 outbox JSON 失败，移入 failed：{result_path.name}，原因：{exc}")
            self._move_file(result_path, self.failed_path)
            return None

        if not isinstance(payload, dict):
            self._append_log(f"outbox JSON 顶层不是对象，移入 failed：{result_path.name}")
            self._move_file(result_path, self.failed_path)
            return None

        return payload

    def _ensure_directories(self) -> None:
        for path in [
            self.inbox_path,
            self.outbox_path,
            self.sent_path,
            self.failed_path,
            self.logs_path,
        ]:
            path.mkdir(parents=True, exist_ok=True)

    def _move_file(self, input_path: Path, target_dir: Path) -> Path:
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = self._unique_path(target_dir / input_path.name)
        shutil.move(str(input_path), str(target_path))
        return target_path

    def _unique_path(self, path: Path) -> Path:
        if not path.exists():
            return path

        for index in range(1, 10_000):
            candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
            if not candidate.exists():
                return candidate

        raise FileExistsError(f"无法生成唯一文件名：{path}")

    def _append_log(self, message: str) -> None:
        self.logs_path.mkdir(parents=True, exist_ok=True)
        with self.log_file_path.open("a", encoding="utf-8") as file:
            file.write(f"{self._now_text()} | {message}\n")

    def _now_text(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _timestamp_for_filename(self) -> str:
        return datetime.now().strftime("%Y%m%d_%H%M%S")


def build_default_wechat_client(config: HarborConfig) -> WxAutoWeChatClient:
    return WxAutoWeChatClient(
        target_contact_name=config.wechat_target_contact_name,
        enable_listener=config.wechat_mode == "listen",
    )


def main() -> None:
    config = load_config()
    adapter = WeChatQueueAdapter.from_config(config)

    if not config.wechat_enabled:
        print("WeChat Queue Adapter 未启用。请先在 config/settings.json 中设置 wechat.enabled=true。")
        return

    try:
        if config.wechat_mode == "send_only":
            print("WeChat Queue Adapter 已启动：send_only。按 Ctrl+C 停止。")
            adapter.run_send_only_forever(lambda: build_default_wechat_client(config))
            return

        if config.wechat_mode != "listen":
            print(f"不支持的 wechat.mode：{config.wechat_mode}")
            return

        client = build_default_wechat_client(config)
    except WeChatUnavailableError as exc:
        adapter._append_log(str(exc))
        print(str(exc))
        return

    print("WeChat Queue Adapter 已启动：listen。按 Ctrl+C 停止。")
    adapter.run_listen_forever(client)


if __name__ == "__main__":
    main()
