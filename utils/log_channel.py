import logging
from config import Config

_logger = logging.getLogger(__name__)


async def send_log(client, text: str):
    """
    Send an event to the global owner LOG_CHANNEL.
    Used for: bot started, bot added/removed from group, new payment.
    """
    if not Config.LOG_CHANNEL:
        return
    try:
        await client.send_message(
            Config.LOG_CHANNEL, text, disable_web_page_preview=True
        )
    except Exception as e:
        _logger.warning(f"LOG_CHANNEL send failed: {e}")


async def send_group_log(client, chat_id: int, text: str):
    """
    Send a moderation event to the group's own premium log channel.
    Used for: member joins, bans, mutes, warns, deleted messages.
    """
    from database.db import db
    log_ch = await db.get_group_log_channel(chat_id)
    if not log_ch:
        return
    try:
        await client.send_message(log_ch, text, disable_web_page_preview=True)
    except Exception as e:
        _logger.warning(f"Group log send failed (chat={chat_id}): {e}")
