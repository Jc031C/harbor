# 0006 - v0.3.3 WeChat send_only Mode

## Status

Accepted for v0.3.3-dev.

## Context

Windows WeChat validation showed that creating a wxauto4 `WeChat` object can bring the real WeChat window to the foreground. The previous eager startup path initialized wxauto4 as soon as `wechat.enabled=true`, even when there were no pending outbox replies.

wxauto4 `Show()` also behaved as a risky UI operation in local tests, so Harbor should not use it as a normal window recovery mechanism.

## Decision

Add `wechat.mode`, defaulting to `send_only`.

In `send_only` mode, WeChat Bridge only checks `data/outbox/`. If there are no pending WeChat replies, it does not initialize wxauto4. If replies exist and `auto_reply=true`, it creates the WeChat client lazily and sends those replies.

The wxauto4 client is initialized as:

```python
WeChat(ads=False, resize=False)
```

The send path must:

1. Call `ChatWith(contact_name, exact=True)`.
2. Call `ChatInfo()`.
3. Verify `chat_name == contact_name`.
4. Call `SendMsg(content)` without passing `contact_name`.

`wx.Show()` is not part of the Harbor main flow.

## Consequences

`enabled=false` remains the safest default and initializes nothing.

`enabled=true` with `mode=send_only` can keep the bridge running without pulling WeChat forward until there is a real outbox reply to send.

`mode=listen` keeps the existing eager-client behavior because incoming message reads require a real WeChat client. Read-side target validation and alternative sub-window approaches remain follow-up work.

## Risks

`ChatWith` is still UI automation and can be unstable. The target check is mandatory before sending. Failed target checks must prevent sending.

Future validation should explore `GetSubWindow` / `GetAllSubWindow` as a possible safer route.
