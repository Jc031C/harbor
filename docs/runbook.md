# Harbor Runbook

## 当前版本

```text
v0.3.3-dev WeChat send_only 懒加载准备
```

v0.3.3-dev 在 wxauto4 兼容准备基础上，增加 `wechat.mode=send_only`。当前 WeChat Queue Adapter 保持文件队列职责不变，并避免在没有待发送 outbox 结果时初始化真实微信客户端。

微信自动化库加载顺序：

- 优先 `wxauto4`
- fallback 到 `wxauto`

真实微信自动化默认关闭：

```json
{
  "wechat": {
    "enabled": false,
    "mode": "send_only"
  }
}
```

默认 `wechat.enabled=false` 时，不会加载真实微信客户端。本阶段不默认连接真实微信，不接入真实大模型 API。

`wechat.mode=send_only` 时，WeChat Bridge 只扫描 `data/outbox/`，不监听微信输入。没有待发送微信结果时，不初始化 wxauto4；有待发送结果时才初始化 wxauto4。wxauto4 初始化可能把微信窗口带到前台，这是已知行为。Harbor 主流程不调用 `wx.Show()`。

发送前必须先 `ChatWith` 切换目标联系人，再用 `ChatInfo` 校验 `chat_name`，校验成功后才执行 `SendMsg(content)`。不要使用 `SendMsg(content, contact_name)` 作为默认发送路径。

## Windows 本地准备

进入项目目录：

```bat
cd /d D:\harbor
```

推荐始终使用项目虚拟环境 Python，避免 WindowsApps 假 Python 抢入口：

```bat
.\.venv\Scripts\python.exe
```

安装当前项目：

```bat
.\.venv\Scripts\python.exe -m pip install -e .
```

运行测试：

```bat
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Windows 微信 4.x 环境建议使用 Python 3.12。`wxauto4` 只在进行真实微信验证时需要安装，不是 Harbor 的强制依赖。

真实微信验证前如需安装 `wxauto4`：

```bat
.\.venv\Scripts\python.exe -m pip install wxauto4
```

只读 import 测试：

```bat
.\.venv\Scripts\python.exe -c "from wxauto4 import WeChat; print('wxauto4 import ok')"
```

Windows PowerShell 临时写 `settings.json` 时可能写入 UTF-8 BOM；Harbor 已兼容 `utf-8-sig`，但仍建议用 Python 写临时 JSON，或使用无 BOM UTF-8。

wxauto4 可能生成 `wxauto_logs/`。该目录是本地运行日志，不纳入 Git。

基础验证：

```bat
scripts\verify_basic.bat
```

## 配置检查

Windows 本地验证前先检查：

```text
config/settings.json
```

默认 Harbor Core 入口建议保持：

```json
{
  "bridge": {
    "default": "local_queue"
  }
}
```

真实微信验证前再按需要配置：

```json
{
  "wechat": {
    "enabled": true,
    "mode": "send_only",
    "target_contact_name": "测试联系人",
    "allowed_senders": ["JC"]
  }
}
```

如果需要监听微信消息，后续使用 `mode=listen`，但该模式会初始化真实微信客户端，仍需单独谨慎验证。

不要把真实联系人、运行数据或临时消息提交到 Git。

## 推荐运行方式

Harbor Core 和 WeChat Bridge 建议分两个窗口运行。

窗口 1：Harbor Core

```bat
cd /d D:\harbor
.\.venv\Scripts\python.exe -m harbor.main
```

窗口 2：WeChat Bridge

```bat
cd /d D:\harbor
.\.venv\Scripts\python.exe -m harbor.bridges.wechat_bridge
```

或者使用 Windows 启动脚本：

```bat
scripts\start_wechat_bridge.bat
```

`start_wechat_bridge.bat` 只启动 WeChat Bridge，不启动 Harbor Core，也不修改配置。

## Local Queue 手动验证

创建文件：

```text
data/inbox/test_mock.json
```

写入：

```json
{
  "source": "local_queue",
  "sender_id": "jc_local",
  "sender_name": "JC",
  "message": "/mock hello harbor"
}
```

运行 Harbor Core：

```bat
.\.venv\Scripts\python.exe -m harbor.main
```

检查：

```text
data/outbox/
data/processed/
data/failed/
data/logs/
```

预期：

- `data/outbox/` 生成结果 JSON
- `data/processed/` 出现原始 JSON 文件
- `data/failed/` 没有新增失败文件
- `data/logs/harbor.log` 有运行日志

## WeChat Bridge 本地验证边界

WeChat Queue Adapter 只负责微信和本地文件队列之间的转换：

- 微信输入写入 `data/inbox/`
- Harbor Core 处理后写入 `data/outbox/`
- WeChat Bridge 只发送明确属于微信来源的 outbox 结果
- 发送成功移动到 `data/wechat/sent/`
- 发送失败移动到 `data/wechat/failed/`

如果 outbox 结果中存在 `source` 字段，必须是 `wechat` 才会发送。如果没有 `source` 字段，才使用 `receiver_id` 以 `wechat_` 开头的兼容规则。

## 切换回 Mock Bridge

修改：

```text
config/settings.json
```

把：

```json
"default": "local_queue"
```

改为：

```json
"default": "mock"
```

然后运行：

```bat
.\.venv\Scripts\python.exe -m harbor.main
```

## 查看日志

普通日志：

```text
data/logs/harbor.log
```

错误日志：

```text
data/logs/errors.log
```

WeChat Bridge 日志：

```text
data/wechat/logs/wechat_bridge.log
```
