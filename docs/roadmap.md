# Harbor Roadmap

## v0.1.0 项目初始化

已完成：

- 基础项目结构
- Harbor Core 最小消息处理器
- Harbor Main Loop 主运行流程
- 本地模拟 Bridge
- Mock LLM Connector
- 本地 Return Channel
- 配置模块
- 日志模块
- 最小测试
- 启动脚本

## v0.2.0 Bridge 本地消息队列原型

目标：

- 不直接接真实微信
- 先增加 inbox / outbox 文件队列
- 模拟外部消息进入 Harbor
- 为后续微信接入做准备
