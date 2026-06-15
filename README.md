# Harbor

Harbor 是一个家庭服务器 Agent 中枢项目。

它的目标不是单独做一个聊天机器人，而是成为家庭服务器的核心调度中心。

当前版本：v0.1.1

## 当前能力

- 本地命令行入口
- Harbor Main Loop 主运行流程
- Harbor Core 最小消息处理
- Mock LLM Connector 占位连接器
- Local Return Channel 本地返回通道
- 配置模块
- 日志模块
- 最小测试
- 启动脚本
- 项目文档

## 本地启动

安装当前项目：

python -m pip install -e .

启动 Harbor：

python -m harbor.main

或者：

bash scripts/run_local.sh

## 运行测试

python -m unittest discover -s tests

或者：

bash scripts/test.sh

## 当前可用指令

- 你好
- 帮助
- 状态
- 问 你的问题
- exit

## 项目结构

harbor/
- docs/：项目文档
- scripts/：启动和测试脚本
- tests/：测试代码
- data/：本地运行数据目录
- src/harbor/：Harbor 主程序代码

## 后续路线

1. v0.2.0：Bridge 本地消息队列原型
2. v0.3.0：GPT Desktop Connector 原型
3. v0.4.0：Return Channel 原型
4. v1.0.0：家庭服务器 Agent 中枢
