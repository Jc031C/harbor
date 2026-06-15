# Harbor Architecture

## v0.3 标准架构

Harbor v0.3 当前推荐运行方式是两个独立进程：

```text
窗口 1：python -m harbor.main
窗口 2：python -m harbor.bridges.wechat_bridge
```

整体链路：

```text
微信消息
-> WeChat Queue Adapter
-> data/inbox/*.json
-> Local Queue Bridge
-> Permission
-> Task
-> Router
-> Worker
-> WorkerResult
-> Logger
-> data/outbox/*.json
-> WeChat Queue Adapter
-> 回复微信
-> data/wechat/sent/ 或 data/wechat/failed/
```

## v0.3 关键边界

WeChat Queue Adapter 是外部适配层，不是 Harbor Core。

它只负责：

- 监听指定微信联系人消息
- 只处理白名单联系人
- 把微信消息转换为 JSON 文件写入 `data/inbox/`
- 从 `data/outbox/` 读取属于微信用户的结果文件
- 把结果中的 `content` 发送回对应微信联系人
- 发送成功后移动结果文件到 `data/wechat/sent/`
- 发送失败后移动结果文件到 `data/wechat/failed/`
- 写入微信桥接日志

它不负责：

- 命令解析
- 权限判断
- Worker 选择
- GPT 调用
- DeepSeek 调用
- LobeChat 调用
- 数据库存储
- 网页后台
- 群聊
- 群发
- 高频自动回复

## Core 主流程

Harbor Core 主流程仍然保持 v0.2 稳定结构：

```text
Mock / Local Queue Bridge
-> Permission
-> Task
-> Router
-> Worker
-> WorkerResult
-> Logger
-> Bridge 输出
```

`main.py` 会根据 `config/settings.json` 中的 `bridge.default` 选择入口：

- `local_queue`：处理当前 `data/inbox/` 中的 JSON 文件后退出
- `mock`：进入本地命令行 Mock Bridge 流程

v0.3 不把 WeChat Queue Adapter 强行绑进 `main.py`。

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

v0.3 当前包含：

- `MockBridge`：本地命令行输入输出，用于开发验证
- `LocalQueueBridge`：本地 JSON 文件消息队列，用于模拟外部消息系统
- `WeChatQueueAdapter`：微信和本地队列之间的独立适配层

Local Queue Bridge 只负责文件读写和消息转交，不负责命令解析、权限判断、Worker 选择或业务执行。

WeChat Queue Adapter 只负责微信收发和本地队列文件转换，不直接操作 Harbor Core。

### Permission

Permission 负责权限检查。

v0.3 当前只做白名单检查。

白名单来自：

```text
config/settings.json
```

注意：WeChat Queue Adapter 也有自己的 `wechat.allowed_senders`，用于在进入 `data/inbox/` 之前先过滤微信联系人。

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

v0.3 当前包含：

- mock_worker：验证本地任务链路
- system_worker：处理 `/help`、`/status` 和未知命令
- gpt_desktop_worker：GPT Desktop 占位回复，不执行真实调用

### Logger

Logger 负责记录 Harbor 运行日志。

Core 日志默认路径：

```text
data/logs/harbor.log
data/logs/errors.log
```

WeChat Queue Adapter 日志默认路径：

```text
data/wechat/logs/wechat_bridge.log
```

## v0.3 不做的事情

Harbor v0.3 不接入：

- 真实 ChatGPT 桌面端
- LobeChat
- DeepSeek API
- 数据库
- 网页后台
- 自然语言智能路由
- 群聊
- 高频自动回复

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
