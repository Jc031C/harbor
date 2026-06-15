# Harbor Roadmap

## v0.1 标准化整理

目标：

- 统一 Task / WorkerResult 命名
- 统一 bridges / workers / core / services 目录职责
- 保留 Mock Bridge 本地验证链路
- 增加 Permission 白名单检查
- 增加 settings.json 配置文件
- 更新 README 和 docs
- 保持测试通过

当前状态：

- Mock Bridge 已完成
- Router 已完成
- Worker 标准结构已完成
- PermissionService 已完成
- LoggerService 已完成
- GPT Desktop Worker 仅为占位模块

## v0.2.0 本地消息队列 Bridge

目标：

- 使用 data/inbox 和 data/outbox 模拟外部消息输入输出
- 为后续微信、网页、企业微信等入口做准备
- 不直接接真实微信

## v0.3.0 GPT Desktop Worker 原型

目标：

- 研究 ChatGPT 桌面端可行接入方式
- 保持 Worker 接口不变
- 不破坏 Task / WorkerResult 主流程

## v0.4.0 外部 Bridge 原型

目标：

- 探索微信或企业微信等外部入口
- 所有外部消息先转换为 Task
- 所有输出统一使用 WorkerResult

## v1.0.0 家庭服务器 Agent 中枢

目标：

- Bridge / Router / Worker / Service 架构稳定
- 支持本地工具和家庭服务器任务
- 支持安全配置、日志、测试和文档
