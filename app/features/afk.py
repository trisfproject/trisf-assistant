import datetime

from app.db import conn
from app.runtime import check_group


async def afk(update, context):
    if not await check_group(update):
        return

    chat = update.effective_chat.id
    user = update.effective_user.id
    reason = " ".join(context.args) if context.args else "AFK"

    cursor = conn.cursor()
    cursor.execute(
        """
        REPLACE INTO afk_status (chat_id,user_id,reason,since)
        VALUES (%s,%s,%s,%s)
        """,
        (chat, user, reason, datetime.datetime.now()),
    )

    await update.message.reply_text(f"AFK: {reason}")
