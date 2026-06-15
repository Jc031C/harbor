# Harbor v0.1 主运行流程设计

日期：2026-06-15

## v0.1 标准主流程

Harbor v0.1 采用以下最小主流程：

Mock Bridge
-> Permission
-> Task
-> Router
-> Worker
-> WorkerResult
-> Logger
-> Mock Bridge 输出

## 当前实现

- Bridge：MockBridge
- Permission：PermissionService
- Task：Task
- Router：Router
- Worker：MockWorker / SystemWorker / GPTDesktopWorker
- WorkerResult：统一执行结果模型
- Logger：LoggerService

## 暂不实现

- 真实微信接入
- 真实 ChatGPT 桌面端接入
- LobeChat 接入
- DeepSeek API 接入
- 自动化操作电脑
- 长期记忆
- 数据库
- 网页后台

## 原因

v0.1 的目标是验证 Harbor 的核心代码结构和本地运行链路，不引入不稳定外部依赖。

后续所有外部入口都应先实现为 Bridge。

后续所有执行能力都应实现为 Worker。

内部主流程保持 Task / WorkerResult 作为统一数据模型。
