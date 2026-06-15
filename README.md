# Harbor

Harbor 是一个家庭服务器 Agent 中枢项目。

它的目标不是单独做一个聊天机器人，而是成为家庭服务器的核心调度中心。

当前版本：v0.1 标准化整理版

## v0.1 当前定位

Harbor v0.1 只做本地运行验证和标准架构整理。

当前不会接入：

- 真实微信
- 真实 ChatGPT 桌面端
- LobeChat
- DeepSeek API
- 数据库
- 网页后台

## v0.1 主流程

Mock Bridge
-> Permission
-> Task
-> Router
-> Worker
-> WorkerResult
-> Logger
-> Mock Bridge 输出

## 当前能力

- Mock Bridge 本地输入输出
- Task 标准任务模型
- WorkerResult 标准执行结果模型
- Router 标准路由
- Mock Worker
- System Worker
- GPT Desktop Worker 占位模块
- Permission 白名单检查
- Logger 日志服务
- settings.json 配置文件
- 单元测试

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

## 当前命令

/mock 内容
/gpt 内容
/help
/status

## 示例

/mock hello harbor
/help
/status
/gpt 测试内容
/abc hello

## 项目结构

harbor/
├─ config/
│  └─ settings.json
├─ docs/
├─ scripts/
├─ tests/
├─ data/
└─ src/harbor/
   ├─ main.py
   ├─ core/
   ├─ bridges/
   ├─ workers/
   ├─ services/
   └─ utils/

## 后续路线

1. v0.2.0：本地消息队列 Bridge
2. v0.3.0：GPT Desktop Worker 原型
3. v0.4.0：外部 Bridge 原型
4. v1.0.0：家庭服务器 Agent 中枢
