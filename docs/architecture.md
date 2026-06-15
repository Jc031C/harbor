# Harbor Architecture

## v0.1 标准架构

Harbor v0.1 当前主流程：

Mock Bridge
-> Permission
-> Task
-> Router
-> Worker
-> WorkerResult
-> Logger
-> Mock Bridge 输出

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

v0.1 当前只启用 Mock Bridge，用于本地命令行输入输出。

后续微信、网页、API 等入口都应该先实现为 Bridge，再转换为 Task。

### Permission

Permission 负责权限检查。

v0.1 当前只做白名单检查。

白名单来自：

config/settings.json

### Router

Router 负责根据 Task.command 选择 Worker。

当前路由规则：

- /mock -> mock_worker
- /gpt -> gpt_desktop_worker
- /help -> system_worker
- /status -> system_worker
- 未知命令 -> system_worker

### Worker

Worker 是实际执行能力。

v0.1 当前包含：

- mock_worker：验证本地任务链路
- system_worker：处理 /help、/status 和未知命令
- gpt_desktop_worker：GPT Desktop 占位回复，不执行真实调用

### Logger

Logger 负责记录 Harbor 运行日志。

日志路径来自：

config/settings.json

## v0.1 不做的事情

Harbor v0.1 不接入：

- 真实微信
- 真实 ChatGPT 桌面端
- LobeChat
- DeepSeek API
- 数据库
- 网页后台

## 当前目录职责

src/harbor/core/

负责核心配置、任务模型和路由。

src/harbor/bridges/

负责外部输入和输出。

src/harbor/workers/

负责执行任务。

src/harbor/services/

负责日志、权限等公共服务。

src/harbor/utils/

负责文本处理等工具函数。
