# Harbor

Harbor 是一个家庭服务器 Agent 中枢项目。

当前版本：v0.1.0

当前能力：

- 本地命令行入口
- Harbor Main Loop 主运行流程
- Harbor Core 最小消息处理
- Mock LLM Connector 占位连接器
- Local Return Channel 本地返回通道
- 配置模块
- 日志模块
- 最小测试

本地启动：

1. 激活虚拟环境
2. 执行 python -m pip install -e .
3. 执行 python -m harbor.main

运行测试：

python -m unittest discover -s tests

当前可用指令：

- 你好
- 帮助
- 状态
- 问 你的问题
- exit
