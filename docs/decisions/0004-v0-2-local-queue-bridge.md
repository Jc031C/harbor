# Harbor v0.2 Local Queue Bridge 设计记录

## 背景

v0.1 已完成标准化骨架：

```text
Bridge -> Permission -> Task -> Router -> Worker -> WorkerResult -> Logger -> Bridge 输出
```

v0.2 的目标是在不接入真实外部平台的情况下，增加一个更接近真实消息系统的本地入口。

## 决策

新增 Local Queue Bridge。

它通过本地目录模拟外部消息队列：

```text
data/inbox/      输入消息 JSON
data/outbox/     输出结果 JSON
data/processed/  成功处理后的原始文件
data/failed/     失败处理后的原始文件
data/logs/       运行日志和错误日志
```

## 主流程

```text
Local Queue Bridge
-> 读取 data/inbox/*.json
-> 转换为 BridgeInput
-> Permission
-> Task
-> Router
-> Worker
-> WorkerResult
-> Logger
-> 写入 data/outbox/
-> 根据结果移动原始文件
```

## 边界

Local Queue Bridge 只负责：

- 文件读取
- JSON 解析
- BridgeInput 生成
- 调用 Harbor 主流程
- 结果文件写入
- 原文件归档到 processed 或 failed

Local Queue Bridge 不负责：

- 命令解析
- 权限判断
- Worker 选择
- GPT 调用
- 微信操作
- 业务逻辑

## 不做项

v0.2 不做：

- 常驻监听
- 复杂并发
- 数据库
- 真实微信
- 真实 ChatGPT 桌面端
- LobeChat
- DeepSeek API
- 网页后台

## 原因

本阶段优先验证 Harbor 的入口扩展能力，而不是引入外部平台复杂度。

Local Queue Bridge 可以让后续微信、企业微信、网页后台或 API 入口先把消息落到统一格式，再逐步升级为真实 Bridge。
