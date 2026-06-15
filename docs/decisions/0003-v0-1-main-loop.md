# Harbor v0.1 主运行流程设计

日期：2026-06-15

## v0.1 决策

Harbor v0.1 采用以下最小主流程：

Bridge
-> HarborRequest
-> HarborMainLoop
-> HarborCore
-> Connector
-> HarborResponse
-> ReturnChannel

## 当前实现

- Bridge：LocalConsoleBridge
- Main Loop：HarborMainLoop
- Core：HarborCore
- Connector：MockLLMConnector
- Return Channel：LocalConsoleReturnChannel

## 暂不实现

- 真实微信接入
- 真实 GPT 桌面端接入
- 自动化操作电脑
- 长期记忆
- 数据库
