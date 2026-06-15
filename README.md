# Harbor

Harbor 是一个家庭服务器 Agent 中枢项目。

它的目标不是单独做一个聊天机器人，而是成为家庭服务器的核心调度中心。

当前版本：v0.3.0 WeChat Queue Adapter 最小可运行版

## v0.3 当前定位

Harbor v0.3 在 v0.2 Local Queue Bridge 基础上，新增 WeChat Queue Adapter。

v0.3 的定位非常明确：

```text
微信消息
-> WeChat Queue Adapter
-> 写入 data/inbox/*.json
-> Harbor v0.2 Local Queue Bridge 处理
-> 写入 data/outbox/*.json
-> WeChat Queue Adapter 读取结果
-> 回复微信
-> 成功移动 result 到 data/wechat/sent/
-> 失败移动 result 到 data/wechat/failed/
```

WeChat Queue Adapter 只负责微信和本地文件队列之间的适配。

它不负责：

- 不解析 `/mock`、`/gpt`、`/help`、`/status`
- 不决定 Worker
- 不调用 GPT
- 不调用 DeepSeek
- 不调用 LobeChat
- 不直接绕过 Permission
- 不直接操作 Harbor Core 业务逻辑
- 不做群聊
- 不做群发
- 不做高频自动回复

## 当前能力

- WeChat Queue Adapter 微信队列适配层
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

## 本地启动 Harbor Core

安装当前项目：

```bash
python -m pip install -e .
```

启动 Harbor Core：

```bash
python -m harbor.main
```

或者：

```bash
bash scripts/run_local.sh
```

`python -m harbor.main` 会根据 `config/settings.json` 里的 `bridge.default` 选择入口。

当前默认配置仍然是：

```json
{
  "bridge": {
    "default": "local_queue",
    "enabled": ["mock", "local_queue", "wechat_queue_adapter"]
  }
}
```

## 独立启动 WeChat Queue Adapter

v0.3 中 WeChat Queue Adapter 是独立运行模块，不和 `python -m harbor.main` 强绑定。

启动方式：

```bash
python -m harbor.bridges.wechat_bridge
```

Windows 也可以使用：

```bat
scripts\start_wechat_bridge.bat
```

默认情况下，真实微信自动化不会启动，因为配置中：

```json
{
  "wechat": {
    "enabled": false
  }
}
```

需要本地真实验证时，再手动修改 `config/settings.json`：

```json
{
  "wechat": {
    "enabled": true,
    "target_contact_name": "你的测试联系人昵称",
    "allowed_senders": ["你的测试联系人昵称"]
  }
}
```

## WeChat Queue Adapter 输入格式

当白名单联系人发送：

```text
/mock hello harbor
```

WeChat Queue Adapter 会写入 `data/inbox/`：

```json
{
  "source": "wechat",
  "sender_id": "wechat_JC",
  "sender_name": "JC",
  "message": "/mock hello harbor",
  "created_at": "2026-06-15 10:00:00"
}
```

然后运行：

```bash
python -m harbor.main
```

Harbor Core 会继续使用 v0.2 Local Queue Bridge 处理该文件。

## WeChat Queue Adapter 输出格式

Harbor Core 处理完成后，`data/outbox/` 会出现类似：

```json
{
  "task_id": "xxx",
  "source": "local_queue",
  "receiver_id": "wechat_JC",
  "receiver_name": "JC",
  "success": true,
  "content": "Mock Worker 已收到：hello harbor",
  "created_at": "2026-06-15 10:00:00"
}
```

WeChat Queue Adapter 会读取 `content`，发送给 `receiver_name` 对应的微信联系人。

发送成功后移动到：

```text
data/wechat/sent/
```

发送失败后移动到：

```text
data/wechat/failed/
```

微信桥接日志写入：

```text
data/wechat/logs/wechat_bridge.log
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

命令仍由 Harbor Core 里的 Router / Worker 处理，WeChat Queue Adapter 不解析命令。

```text
/mock 内容
/gpt 内容
/help
/status
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
│  ├─ logs/
│  └─ wechat/
│     ├─ sent/
│     ├─ failed/
│     └─ logs/
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

1. v0.1.0：标准化核心骨架，已完成
2. v0.2.0：Local Queue Bridge，已完成
3. v0.3.0：WeChat Queue Adapter，已完成
4. v0.4.0：GPT Desktop Worker 原型
5. v1.0.0：家庭服务器 Agent 中枢
