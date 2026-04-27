from app.db import conn
from app.messages import ACCESS_DENIED
from app.runtime import check_group, is_admin


def ensure_oncall_schema():
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS oncall_status (
            chat_id BIGINT PRIMARY KEY,
            user_id BIGINT,
            username TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA=DATABASE()
        AND TABLE_NAME='oncall_status'
        """
    )

    columns = {row[0] for row in cursor.fetchall()}

    if "username" not in columns:
        cursor.execute(
            """
            ALTER TABLE oncall_status
            ADD COLUMN username TEXT
            """
        )


async def oncall_status(update, context):
    if not await check_group(update):
        return

    ensure_oncall_schema()

    chat = update.effective_chat.id
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT user_id,username
        FROM oncall_status
        WHERE chat_id=%s
        """,
        (chat,),
    )

    row = cursor.fetchone()

    if not row:
        await update.message.reply_text("Tidak ada on-call aktif")
        return

    user_id, username = row
    user = username.strip() if username else str(user_id)

    if user and not user.startswith("@"):
        user = f"@{user}"

    await update.message.reply_text(f"On-call sekarang: {user}")


async def oncall_set(update, context):
    if not await is_admin(update, context):
        await update.message.reply_text(ACCESS_DENIED)
        return

    if len(context.args) < 2:
        await update.message.reply_text("usage: /oncall set @username")
        return

    ensure_oncall_schema()

    chat = update.effective_chat.id
    username = context.args[1].strip()
    user_id = None

    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        user_id = user.id
        username = user.username or username

    if username.startswith("@"):
        username = username[1:]

    cursor = conn.cursor()
    cursor.execute(
        """
        REPLACE INTO oncall_status (chat_id,user_id,username,updated_at)
        VALUES (%s,%s,%s,NOW())
        """,
        (chat, user_id, username),
    )

    await update.message.reply_text(f"On-call updated: @{username}")


async def oncall_clear(update, context):
    if not await is_admin(update, context):
        await update.message.reply_text(ACCESS_DENIED)
        return

    ensure_oncall_schema()

    chat = update.effective_chat.id
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM oncall_status WHERE chat_id=%s",
        (chat,),
    )

    await update.message.reply_text("On-call cleared")


async def oncall_handler(update, context):
    if not context.args or context.args[0].lower() == "status":
        await oncall_status(update, context)
        return

    command = context.args[0].lower()

    if command == "set":
        await oncall_set(update, context)
        return

    if command == "clear":
        await oncall_clear(update, context)
        return

    await update.message.reply_text("usage: /oncall status|set @username|clear")
