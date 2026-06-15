# Harbor Architecture

## v0.2 标准架构

Harbor v0.2 当前默认主流程：

```text
Local Queue Bridge
-> 读取 data/inbox/*.json
-> Permission
-> Task
-> Router
-> Worker
-> WorkerResult
-> Logger
-> 写入 data/outbox/*.json
-> 成功移动原文件到 data/processed/
-> 失败移动原文件到 data/failed/
```

v0.2 仍保留 v0.1 的 Mock Bridge，用于本地命令行验证。

`main.py` 会根据 `config/settings.json` 中的 `bridge.default` 选择入口：

- `local_queue`：处理当前 `data/inbox/` 中的 JSON 文件后退出
- `mock`：进入本地命令行 Mock Bridge 流程

## 核心概念

### Task

Task 是 Harbor 内部统一任务模型。

外部输入进入 Harbor 后，会先经过 Bridge，再被转换为 Task。

Task 当前包含：

- source：任务来源
- sender：发送者
- raw_text：原始输入文本
- command：解析后的命令
- content：命令后面的正文内容
- metadata：扩展信息

### WorkerResult

WorkerResult 是 Harbor 内部统一执行结果模型。

所有 Worker 执行任务后，都必须返回 WorkerResult。

WorkerResult 当前包含：

- success：是否执行成功
- message：返回信息
- worker_name：处理该任务的 Worker 名称
- metadata：扩展信息

### Bridge

Bridge 是外部入口和出口。

v0.2 当前包含：

- `MockBridge`：本地命令行输入输出，用于开发验证
- `LocalQueueBridge`：本地 JSON 文件消息队列，用于模拟外部消息系统
- `WechatBridge`：占位模块，当前不接真实微信

Local Queue Bridge 只负责文件读写和消息转交，不负责命令解析、权限判断、Worker 选择或业务执行。

### Permission

Permission 负责权限检查。

v0.2 当前只做白名单检查。

白名单来自：

```text
config/settings.json
```

### Router

Router 负责根据 Task.command 选择 Worker。

当前路由规则：

- `/mock` -> mock_worker
- `/gpt` -> gpt_desktop_worker
- `/help` -> system_worker
- `/status` -> system_worker
- 未知命令 -> system_worker

### Worker

Worker 是实际执行能力。

v0.2 当前包含：

- mock_worker：验证本地任务链路
- system_worker：处理 `/help`、`/status` 和未知命令
- gpt_desktop_worker：GPT Desktop 占位回复，不执行真实调用

### Logger

Logger 负责记录 Harbor 运行日志。

日志路径来自：

```text
config/settings.json
```

默认路径：

```text
data/logs/harbor.log
data/logs/errors.log
```

## v0.2 不做的事情

Harbor v0.2 不接入：

- 真实微信
- 真实 ChatGPT 桌面端
- LobeChat
- DeepSeek API
- 数据库
- 网页后台
- 复杂并发
- 常驻监听

## 当前目录职责

```text
src/harbor/core/
```

负责核心配置、任务模型和路由。

```text
src/harbor/bridges/
```

负责外部输入和输出。

```text
src/harbor/workers/
```

负责执行任务。

```text
src/harbor/services/
```

负责日志、权限等公共服务。

```text
src/harbor/utils/
```

负责文本处理等工具函数。
