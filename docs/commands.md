# Harbor Commands

Harbor v0.2 当前支持以下命令。

命令可以通过 Mock Bridge 输入，也可以写入 Local Queue Bridge 的 JSON 文件中。

## /mock

用途：

验证 Mock Worker 链路。

示例：

```text
/mock hello harbor
```

路由结果：

```text
/mock -> mock_worker
```

预期效果：

Mock Worker 返回收到的内容。

## /gpt

用途：

验证 GPT Desktop Worker 占位模块。

示例：

```text
/gpt 测试内容
```

路由结果：

```text
/gpt -> gpt_desktop_worker
```

注意：

v0.2 不接入真实 ChatGPT 桌面端，只返回占位回复。

## /help

用途：

查看 Harbor 当前可用命令。

路由结果：

```text
/help -> system_worker
```

## /status

用途：

查看 Harbor 当前运行状态。

路由结果：

```text
/status -> system_worker
```

## 未知命令

示例：

```text
/abc hello
```

路由结果：

```text
未知命令 -> system_worker
```

System Worker 会返回提示，让用户使用 `/help` 查看支持的命令。

## Local Queue 输入示例

文件路径：

```text
data/inbox/test_mock.json
```

文件内容：

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

处理后会生成：

```text
data/outbox/test_mock.result.json
```

成功时原文件会移动到：

```text
data/processed/test_mock.json
```

失败时原文件会移动到：

```text
data/failed/test_mock.json
```
