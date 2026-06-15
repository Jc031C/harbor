# Harbor Commands

Harbor v0.1 当前支持以下命令。

## /mock

用途：

验证 Mock Worker 链路。

示例：

/mock hello harbor

路由结果：

/mock -> mock_worker

预期效果：

Mock Worker 返回收到的内容。

## /gpt

用途：

验证 GPT Desktop Worker 占位模块。

示例：

/gpt 测试内容

路由结果：

/gpt -> gpt_desktop_worker

注意：

v0.1 不接入真实 ChatGPT 桌面端，只返回占位回复。

## /help

用途：

查看 Harbor v0.1 可用命令。

路由结果：

/help -> system_worker

## /status

用途：

查看 Harbor 当前运行状态。

路由结果：

/status -> system_worker

## 未知命令

示例：

/abc hello

路由结果：

未知命令 -> system_worker

System Worker 会返回提示，让用户使用 /help 查看支持的命令。
