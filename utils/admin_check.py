from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus

async def is_admin(client, message: Message) -> bool:
    # FIX: When a user posts as the group (anonymous admin), from_user is None.
    # Previously this caused an AttributeError on .id — now we treat it as non-admin.
    if not message.from_user:
        return False
    if message.chat.type.value == "private":
        return True
    try:
        member = await client.get_chat_member(message.chat.id, message.from_user.id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception:
        return False
