# Harbor

Harbor 是一个家庭服务器 Agent 中枢项目。

它的目标不是单独做一个聊天机器人，而是成为家庭服务器的核心调度中心。

当前版本：v0.2.0 Local Queue Bridge 最小可运行版

## v0.2 当前定位

Harbor v0.2 在 v0.1 标准化骨架基础上，新增本地文件消息队列 Bridge。

当前默认入口是 Local Queue Bridge：

```text
Local Queue Bridge
-> 读取 data/inbox/*.json
-> Permission
-> Task
-> Router
-> Worker
-> WorkerResult
-> Logger
-> 写入 data/outbox/*.json
-> 成功移动原文件到 data/processed/
-> 失败移动原文件到 data/failed/
```

当前不会接入：

- 真实微信
- 真实 ChatGPT 桌面端
- LobeChat
- DeepSeek API
- 数据库
- 网页后台
- 复杂并发
- 常驻监听

## 当前能力

- Local Queue Bridge 本地 JSON 文件输入输出
- Mock Bridge 本地命令行输入输出
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

```bash
python -m pip install -e .
```

启动 Harbor：

```bash
python -m harbor.main
```

或者：

```bash
bash scripts/run_local.sh
```

`python -m harbor.main` 会根据 `config/settings.json` 里的 `bridge.default` 选择入口。

当前默认配置：

```json
{
  "bridge": {
    "default": "local_queue",
    "enabled": ["mock", "local_queue"]
  }
}
```

## Local Queue 使用示例

创建输入文件：

```text
data/inbox/test_mock.json
```

写入内容：

```json
{
  "source": "local_queue",
  "sender_id": "jc_local",
  "sender_name": "JC",
  "message": "/mock hello harbor"
}
```

运行：

```bash
python -m harbor.main
```

预期结果：

- `data/outbox/` 生成结果 JSON
- `data/processed/` 出现原始输入文件
- `data/failed/` 保持为空
- `data/logs/harbor.log` 记录运行日志

## 运行测试

```bash
python -m unittest discover -s tests
```

或者：

```bash
bash scripts/test.sh
```

## 当前命令

```text
/mock 内容
/gpt 内容
/help
/status
```

## 示例

```text
/mock hello harbor
/help
/status
/gpt 测试内容
/abc hello
```

## 项目结构

```text
harbor/
├─ config/
│  └─ settings.json
├─ data/
│  ├─ inbox/
│  ├─ outbox/
│  ├─ processed/
│  ├─ failed/
│  └─ logs/
├─ docs/
├─ scripts/
├─ tests/
└─ src/harbor/
   ├─ main.py
   ├─ core/
   ├─ bridges/
   ├─ workers/
   ├─ services/
   └─ utils/
```

## 后续路线

1. v0.2.0：本地消息队列 Bridge，已完成
2. v0.3.0：GPT Desktop Worker 原型
3. v0.4.0：外部 Bridge 原型
4. v1.0.0：家庭服务器 Agent 中枢
