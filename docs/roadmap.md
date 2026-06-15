# Harbor Roadmap

## v0.1.0 标准化整理

目标：

- 统一 Task / WorkerResult 命名
- 统一 bridges / workers / core / services 目录职责
- 保留 Mock Bridge 本地验证链路
- 增加 Permission 白名单检查
- 增加 settings.json 配置文件
- 更新 README 和 docs
- 保持测试通过

当前状态：已完成。

## v0.2.0 Local Queue Bridge

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

## v0.3.0 WeChat Queue Adapter

目标：

- 微信作为 Harbor 的外部入口和出口
- 微信模块只和本地队列交互
- 微信输入写入 `data/inbox/`
- Harbor Core 继续由 Local Queue Bridge 处理
- Harbor 输出写入 `data/outbox/`
- 微信模块读取 outbox 并回复联系人
- 发送成功移动到 `data/wechat/sent/`
- 发送失败移动到 `data/wechat/failed/`
- 真实微信自动化默认关闭
- 单元测试使用 mock 微信客户端，不依赖真实微信环境

当前状态：已完成。

已完成内容：

- `src/harbor/bridges/wechat_bridge.py` 已实现 WeChat Queue Adapter
- `config/settings.json` 已新增 `wechat` 配置
- 新增 `data/wechat/sent/`、`data/wechat/failed/`、`data/wechat/logs/`
- 新增 `tests/test_wechat_bridge.py`
- 新增 `scripts/start_wechat_bridge.bat`
- `pyproject.toml` 已升级到 v0.3.0
- README 和 docs 已同步到 v0.3.0
- 旧 v0.1 / v0.2 测试仍然通过

## v0.4.0 GPT Desktop Worker 原型

目标：

- 研究 ChatGPT 桌面端可行接入方式
- 保持 Worker 接口不变
- 不破坏 Task / WorkerResult 主流程
- 不让 Bridge 直接调用 GPT

当前状态：未开始。

## v1.0.0 家庭服务器 Agent 中枢

目标：

- Bridge / Router / Worker / Service 架构稳定
- 支持本地工具和家庭服务器任务
- 支持安全配置、日志、测试和文档
