# Harbor Modules

## src/harbor/main.py

Harbor 主入口。

负责组装并执行 v0.1 主流程：

- Config
- Logger
- PermissionService
- Router
- MockBridge

## src/harbor/core/

核心模块。

### config.py

读取配置文件：

config/settings.json

提供 HarborConfig。

### task.py

定义 Harbor v0.1 标准模型：

- Task
- WorkerResult

### router.py

根据 Task.command 选择 Worker。

当前规则：

- /mock -> mock_worker
- /gpt -> gpt_desktop_worker
- /help -> system_worker
- /status -> system_worker
- 未知命令 -> system_worker

## src/harbor/bridges/

Bridge 层。

Bridge 负责外部输入和输出。

### base_bridge.py

定义：

- BridgeInput
- BaseBridge 协议

### mock_bridge.py

v0.1 本地命令行 Bridge。

用于本地运行验证。

### wechat_bridge.py

微信 Bridge 占位模块。

v0.1 不接入真实微信。

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

- /help
- /status
- 未知命令

### gpt_desktop_worker.py

GPT Desktop Worker 占位模块。

v0.1 不执行真实 ChatGPT 桌面端调用。

## src/harbor/services/

公共服务层。

### logger_service.py

负责创建和管理日志。

### permission_service.py

负责白名单权限检查。

白名单来自：

config/settings.json

## src/harbor/utils/

工具模块。

### text_utils.py

负责文本清洗和命令解析。
