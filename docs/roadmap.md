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

当前状态：已完成。

## v0.2.0 本地消息队列 Bridge

目标：

- 使用 `data/inbox/` 和 `data/outbox/` 模拟外部消息输入输出
- 成功处理后将原文件移动到 `data/processed/`
- 失败处理后将原文件移动到 `data/failed/`
- 根据 `config/settings.json` 的 `bridge.default` 选择 `mock` 或 `local_queue`
- 为后续微信、网页、企业微信等入口做准备
- 不直接接真实微信
- 不做常驻监听
- 不做复杂并发

当前状态：已完成。

已完成内容：

- Local Queue Bridge 已完成
- `data/inbox/`、`data/outbox/`、`data/processed/`、`data/failed/` 目录已保留
- `settings.json` 已升级到 v0.2.0
- `pyproject.toml` 已升级到 v0.2.0
- `main.py` 已支持根据配置选择 Bridge
- Local Queue 相关测试已加入
- 旧 v0.1 测试仍然通过

## v0.3.0 GPT Desktop Worker 原型

目标：

- 研究 ChatGPT 桌面端可行接入方式
- 保持 Worker 接口不变
- 不破坏 Task / WorkerResult 主流程
- 不让 Bridge 直接调用 GPT

## v0.4.0 外部 Bridge 原型

目标：

- 探索微信或企业微信等外部入口
- 所有外部消息先转换为 Task
- 所有输出统一使用 WorkerResult
- 保持权限、日志、路由独立

## v1.0.0 家庭服务器 Agent 中枢

目标：

- Bridge / Router / Worker / Service 架构稳定
- 支持本地工具和家庭服务器任务
- 支持安全配置、日志、测试和文档
