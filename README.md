# astrbot_plugin_disclaimer_filter

免责声明同意状态检查插件 — 拦截未同意免责声明的用户，保护服务提供方。

## 功能

- 在 Bot 被唤醒（@/私聊/唤醒词）时，通过 API 实时查询用户是否已同意免责声明
- 已同意 → 放行；未同意 → 回复提示并阻止 LLM 调用，不消耗 token
- 群聊中无人@bot 时完全静默，不插嘴
- 已同意的用户缓存结果，减少 API 压力
- 未同意的用户每次实时查询，同意后立即可用
- 管理员白名单直接放行

## 配置

| 配置项 | 类型 | 说明 |
|--------|------|------|
| `api_url` | string | 免责声明同意状态查询 API 地址 |
| `reply_on_block` | text | 拦截时发送给用户的提示消息 |
| `admin_ids` | list | 管理员 QQ 号白名单 |

## 依赖

- aiohttp（AstrBot 内置依赖，无需额外安装）

## 配套服务端

本插件需要配合免责声明同意系统使用，可以通过以下开源项目一键部署到自己的服务器/网站：

👉 **[Wyccotccy/disclaimer-consent](https://github.com/Wyccotccy/disclaimer-consent)**

这是一个轻量级的免责声明同意管理系统，支持：
- 完整的免责声明展示页面（v4.0）
- 用户点击同意后记录到 SQLite 数据库
- API 接口供机器人查询用户的同意状态
- 防重复提交（同 QQ/IP/设备指纹）
- 内置简易管理面板
- 无外部依赖，PHP 8.0+ + SQLite 即可运行

## 工作原理

```
群消息 → bot未唤醒 → 完全跳过，不检查不回复
群消息 → @bot      → 查 API → 已同意→放行 → LLM 回复
                              → 未同意→拦截提示+stop_event
私聊 → 查 API → 已同意→放行
              → 未同意→拦截提示
```

## License

MIT
