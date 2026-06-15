# Harbor Runbook

## 当前版本

```text
v0.2.0 Local Queue Bridge
```

## 本地启动

进入项目目录：

```bash
cd /workspaces/harbor
```

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

## 运行测试

```bash
python -m unittest discover -s tests
```

或者：

```bash
bash scripts/test.sh
```

## Local Queue 手动验证

确认 `config/settings.json` 中默认 Bridge 是：

```json
{
  "bridge": {
    "default": "local_queue"
  }
}
```

创建文件：

```text
data/inbox/test_mock.json
```

写入：

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

检查：

```text
data/outbox/
data/processed/
data/failed/
data/logs/
```

预期：

- `data/outbox/` 生成结果 JSON
- `data/processed/` 出现原始 JSON 文件
- `data/failed/` 没有新增失败文件
- `data/logs/harbor.log` 有运行日志

## 切换回 Mock Bridge

修改：

```text
config/settings.json
```

把：

```json
"default": "local_queue"
```

改为：

```json
"default": "mock"
```

然后运行：

```bash
python -m harbor.main
```

## 查看日志

普通日志：

```text
data/logs/harbor.log
```

错误日志：

```text
data/logs/errors.log
```
