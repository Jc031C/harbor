# Harbor Architecture

## v0.1 当前架构

Local Console
-> LocalConsoleBridge
-> HarborRequest
-> HarborMainLoop
-> HarborCore
-> MockLLMConnector
-> HarborResponse
-> LocalConsoleReturnChannel

## 目标架构

微信 / 网页 / API / 其他入口
-> Bridge 层
-> HarborRequest
-> Harbor Core
-> Connector 层
-> GPT Desktop / LLM / 本地工具 / 家庭服务器任务
-> HarborResponse
-> Return Channel 层
-> 微信 / 网页 / 邮件 / 通知
