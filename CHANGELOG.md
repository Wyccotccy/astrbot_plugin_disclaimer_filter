# Changelog

## v1.0.0 (2026-05-22)

- 初始版本
- 基于 `@filter.event_message_type(ALL)` 在消息管道早期拦截
- 群聊非唤醒消息静默跳过
- LLM 请求通过 `stop_event()` + `should_call_llm(False)` 双重阻止，不消耗 token
- 已同意用户缓存放行，未同意用户实时查询
