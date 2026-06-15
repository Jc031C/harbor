# Harbor Modules

## src/harbor/main.py

Harbor 主入口。

负责组装并执行 v0.2 主流程：

- Config
- Logger
- PermissionService
- Router
- Bridge
- WorkerResult 输出

`main.py` 会根据 `config/settings.json` 里的 `bridge.default` 选择入口：

- `local_queue`：处理 `data/inbox/` 中当前存在的 JSON 文件后退出
- `mock`：进入本地命令行 Mock Bridge 流程

## src/harbor/core/

核心模块。

### config.py

读取配置文件：

```text
config/settings.json
```

提供 HarborConfig。

v0.2 已支持读取：

- app 版本
- bridge 默认入口
- local_queue 路径配置
- workers 配置
- permission 白名单
- logs 路径

### task.py

定义 Harbor 标准模型：

- Task
- WorkerResult

### router.py

根据 Task.command 选择 Worker。

当前规则：

- `/mock` -> mock_worker
- `/gpt` -> gpt_desktop_worker
- `/help` -> system_worker
- `/status` -> system_worker
- 未知命令 -> system_worker

## src/harbor/bridges/

Bridge 层。

Bridge 负责外部输入和输出。

### base_bridge.py

定义：

- BridgeInput
- BaseBridge 协议

### mock_bridge.py

本地命令行 Bridge。

用于本地运行验证。

### local_queue_bridge.py

v0.2 新增的本地文件消息队列 Bridge。

职责：

- 读取 `data/inbox/*.json`
- 解析输入 JSON
- 自动补齐 `created_at`
- 转换为 BridgeInput
- 调用 Harbor 主流程处理
- 将结果写入 `data/outbox/`
- 成功后移动原文件到 `data/processed/`
- 失败后移动原文件到 `data/failed/`

不负责：

- 命令解析
- Worker 选择
- 权限判断
- GPT 调用
- 微信操作
- 复杂业务逻辑

### wechat_bridge.py

微信 Bridge 占位模块。

v0.2 不接入真实微信。

## src/harbor/workers/

Worker 层。

Worker 负责执行具体任务，并返回 WorkerResult。

### base_worker.py

定义 BaseWorker 协议。

### mock_worker.py

Mock Worker。

用于验证 Task -> Router -> Worker -> WorkerResult 链路。

### system_worker.py

System Worker。

负责处理：

- `/help`
- `/status`
- 未知命令

### gpt_desktop_worker.py

GPT Desktop Worker 占位模块。

v0.2 不执行真实 ChatGPT 桌面端调用。

## src/harbor/services/

公共服务层。

### logger_service.py

负责创建和管理日志。

### permission_service.py

负责白名单权限检查。

白名单来自：

```text
config/settings.json
```

## src/harbor/utils/

工具模块。

### text_utils.py

负责文本清洗和命令解析。
