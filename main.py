"""
disclaimer_filter - 免责协议同意状态检查插件

原理：
1. 用 @filter.event_message_type(ALL) 在所有 handler 之前拦截
2. 已同意 → 放行；未同意 → stop_event + should_call_llm(False)
3. 仅在 bot 被唤醒（@/私聊/唤醒词）时回复提示，群聊无关消息静默拦截不回复
4. LLM 被 should_call_llm(False) + stop_event 双重阻止，不消耗 token

依赖：aiohttp (AstrBot 内置)
"""

import asyncio
from typing import Dict, Any, Optional

import aiohttp

from astrbot.api.star import Context, Star, register
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api import logger


@register("disclaimer_filter", "cinder", "免责协议同意状态检查", "1.0.0")
class DisclaimerFilter(Star):
    """免责声明同意状态检查插件"""

    def __init__(self, context: Context, config: Optional[Dict[str, Any]] = None):
        super().__init__(context)
        self.config = config or {}
        self.api_url = self.config.get(
            "api_url",
            "https://cinder.wyccotccy.cn/api/disclaimer?qq="
        )
        self.reply_msg = self.config.get(
            "reply_on_block",
            "⚠️ 您尚未同意免责声明，无法使用本机器人。\n请前往 https://cinder.wyccotccy.cn/disclaimer 阅读并同意免责声明后，再使用本机器人。"
        )
        self.admin_ids = self.config.get("admin_ids", ["1449783068", "2280158744"])
        self._cache: Dict[str, bool] = {}

        logger.info(
            f"[DisclaimerFilter] 已加载 | API: {self.api_url} | "
            f"管理员: {self.admin_ids}"
        )

    async def _check_consent(self, qq: str) -> Optional[bool]:
        """
        查询免责同意状态。
        - 已同意 → 缓存结果，下次直接放行
        - 未同意/查询失败 → 不缓存，每次都重新查
        """
        if qq in self._cache:
            return True  # 缓存里只存已同意的用户

        url = f"{self.api_url.rstrip('?&')}{qq}"

        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        logger.warning(f"[DisclaimerFilter] API {resp.status}")
                        return None
                    data = await resp.json()
                    consented = data.get("data", {}).get("consented", False)
                    if consented:
                        self._cache[qq] = True  # 仅缓存已同意的用户
                    return consented
        except asyncio.TimeoutError:
            logger.warning(f"[DisclaimerFilter] 超时 (QQ: {qq})")
            return None
        except Exception as e:
            logger.error(f"[DisclaimerFilter] 异常: {e}")
            return None

    # ========== 消息拦截 ==========
    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent):
        """
        在消息管道早期拦截，检查免责同意状态。
        - 群聊里 bot 没被唤醒 → 不做任何事（不发消息，不检查 API）
        - bot 被唤醒但用户未同意 → 回复提示 + 完全阻止 LLM
        """
        sender_id = event.get_sender_id()
        if not sender_id:
            return

        # 管理员白名单直接放行
        if sender_id in self.admin_ids:
            return

        # 只有 bot 被唤醒时才需要检查（私聊/@bot/唤醒词）
        # 群聊没被@时的消息：bot 本来就不会回复，我们也不该回复
        if not event.is_at_or_wake_command:
            return

        consented = await self._check_consent(sender_id)

        if consented is True:
            return  # 已同意，放行

        if consented is False:
            logger.info(
                f"[DisclaimerFilter] 拦截未同意 {sender_id} "
                f"({event.get_group_id() or '私聊'})"
            )
            # 回复提示 + 双重阻止 LLM
            yield event.plain_result(self.reply_msg)
            event.stop_event()
            event.should_call_llm(False)
            return

        if consented is None:
            # 查询失败：阻止 LLM 但静默（不发消息）
            logger.warning(
                f"[DisclaimerFilter] 查询失败，静默阻止 LLM (QQ: {sender_id})"
            )
            event.stop_event()
            event.should_call_llm(False)
            return

    async def terminate(self):
        """插件卸载时清理"""
        self._cache.clear()
        logger.info("[DisclaimerFilter] 已卸载")
