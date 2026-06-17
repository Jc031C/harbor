# 0005 - v0.3.2 wxauto4 Loader

## Status

Accepted.

## Context

Harbor v0.3.2 is not a real WeChat integration release. Its purpose is to prepare the WeChat Queue Adapter for Windows WeChat 4.x validation while keeping the Harbor Core architecture unchanged.

The existing WeChat path remains:

```text
WeChat
-> WeChat Queue Adapter
-> data/inbox
-> Harbor Core
-> data/outbox
-> WeChat Queue Adapter
-> reply to WeChat
```

WeChat Bridge must not call Router, Worker, GPT Desktop, or other Harbor Core business logic directly.

## Decision

Add `src/harbor/bridges/wechat_client_loader.py` as the single place that loads optional WeChat automation libraries.

The loading order is:

1. `wxauto4`
2. `wxauto`

If both imports fail, the loader returns a clear error. Harbor Core does not directly depend on `wxauto` or `wxauto4`, and these packages are not required for normal local queue, mock bridge, router, worker, permission, or logger flows.

`wechat.enabled` remains `false` by default. When disabled, WeChat Bridge exits safely and does not load a real WeChat client.

## Consequences

The v0.3.2 change should not affect:

- Local Queue Bridge
- Mock Bridge
- Permission checks
- Task creation
- Router behavior
- Worker execution
- WorkerResult handling
- Logger behavior

Real Windows WeChat verification remains a separate follow-up step.
