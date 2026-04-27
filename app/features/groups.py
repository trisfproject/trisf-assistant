from app.db import conn
from app.messages import ACCESS_DENIED
from app.permissions import is_superuser


def ensure_allowed_groups_table():
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS allowed_groups (
            chat_id BIGINT PRIMARY KEY,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


async def allowgroup(update, context):
    if not is_superuser(update.effective_user.id):
        await update.message.reply_text(ACCESS_DENIED)
        return

    ensure_allowed_groups_table()

    chat = update.effective_chat.id
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT IGNORE INTO allowed_groups (chat_id)
        VALUES (%s)
        """,
        (chat,),
    )

    await update.message.reply_text("👥 Group allowed")


async def removegroup(update, context):
    if not is_superuser(update.effective_user.id):
        await update.message.reply_text(ACCESS_DENIED)
        return

    ensure_allowed_groups_table()

    chat = update.effective_chat.id
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM allowed_groups WHERE chat_id=%s",
        (chat,),
    )

    await update.message.reply_text("👥 Group removed")


async def allowedgroups(update, context):
    if not is_superuser(update.effective_user.id):
        await update.message.reply_text(ACCESS_DENIED)
        return

    ensure_allowed_groups_table()

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT chat_id
        FROM allowed_groups
        ORDER BY chat_id
        """
    )

    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("👥 No allowed groups found")
        return

    msg = "👥 Allowed groups:\n\n"
    for row in rows:
        msg += f"{row[0]}\n"

    await update.message.reply_text(msg)
