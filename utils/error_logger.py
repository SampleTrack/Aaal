import logging
import os
from functools import wraps

# Create logs directory on startup (ephemeral on Render, resets on redeploy — expected)
os.makedirs("logs", exist_ok=True)

# ── File handler: errors only ──────────────────────────────────────────────
_err_fh = logging.FileHandler("logs/bot_errors.log", encoding="utf-8")
_err_fh.setLevel(logging.ERROR)
_err_fh.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
))

# ── File handler: every command execution ──────────────────────────────────
_act_fh = logging.FileHandler("logs/commands.log", encoding="utf-8")
_act_fh.setLevel(logging.INFO)
_act_fh.setFormatter(logging.Formatter(
    "%(asctime)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
))

error_logger = logging.getLogger("bot.errors")
error_logger.setLevel(logging.ERROR)
if not error_logger.handlers:
    error_logger.addHandler(_err_fh)

activity_logger = logging.getLogger("bot.activity")
activity_logger.setLevel(logging.INFO)
if not activity_logger.handlers:
    activity_logger.addHandler(_act_fh)


def log_command(func):
    """
    Decorator for Pyrogram command handlers (owner-only logging).
    - Logs every invocation to  logs/commands.log
    - On any exception, writes full traceback to logs/bot_errors.log
      and replies to the user with a clean error notice.
    """
    @wraps(func)
    async def wrapper(client, message, *args, **kwargs):
        user_id = message.from_user.id if message.from_user else "anon"
        chat_id = message.chat.id
        cmd = (
            message.command[0]
            if hasattr(message, "command") and message.command
            else func.__name__
        )
        activity_logger.info(f"/{cmd} | user={user_id} | chat={chat_id}")
        try:
            return await func(client, message, *args, **kwargs)
        except Exception as e:
            error_logger.error(
                f"/{cmd} | user={user_id} | chat={chat_id} | {type(e).__name__}: {e}",
                exc_info=True,
            )
            try:
                await message.reply(
                    f"❌ An internal error occurred in `/{cmd}`.\nIt has been saved to the error log."
                )
            except Exception:
                pass
    return wrapper
