from app.db import conn
from app.messages import ACCESS_DENIED, WRITE_DENIED
from app.permissions import is_writer
from app.runtime import check_group, is_admin, log_action


async def save(update, context):

    if not await check_group(update):
        return

    chat = update.effective_chat.id
    user = update.effective_user.id

    if not is_writer(chat, user):
        await update.message.reply_text(WRITE_DENIED)
        return

    if len(context.args) < 2:
        return

    key = context.args[0]
    content = " ".join(context.args[1:])

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT IGNORE INTO saved_notes
        (chat_id,key_name,content,created_by)
        VALUES (%s,%s,%s,%s)
        """,
        (chat, key, content, user),
    )

    if cursor.rowcount == 0:
        await update.message.reply_text(
            "⚠️ key sudah ada gunakan /update"
        )
        return

    log_action(chat, user, "save", key)

    await update.message.reply_text("✅ saved")


async def update_note(update, context):

    if not await is_admin(update, context):
        await update.message.reply_text(ACCESS_DENIED)
        return

    chat = update.effective_chat.id

    if not context.args:
        return

    key = context.args[0]
    content = " ".join(context.args[1:])

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE saved_notes
        SET content=%s,updated_at=NOW()
        WHERE chat_id=%s AND key_name=%s
        """,
        (content, chat, key),
    )

    log_action(chat, update.effective_user.id, "update", key)

    await update.message.reply_text("✅ updated")


async def delete(update, context):

    if not await is_admin(update, context):
        await update.message.reply_text(ACCESS_DENIED)
        return

    chat = update.effective_chat.id

    if not context.args:
        return

    key = context.args[0]

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM saved_notes
        WHERE chat_id=%s AND key_name=%s
        """,
        (chat, key),
    )

    log_action(chat, update.effective_user.id, "delete", key)

    await update.message.reply_text("🗑 deleted")


async def notes(update, context):

    if not await check_group(update):
        return

    chat = update.effective_chat.id

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT key_name
        FROM saved_notes
        WHERE chat_id=%s
        ORDER BY key_name
        """,
        (chat,),
    )

    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("belum ada notes")
        return

    msg = "Available notes:\n\n"

    for r in rows:
        msg += r[0] + "\n"

    await update.message.reply_text(msg)


async def lookup(update, context):

    if not await check_group(update):
        return

    chat = update.effective_chat.id

    key = update.message.text.split()[0][1:]

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT content
        FROM saved_notes
        WHERE chat_id=%s AND key_name=%s
        """,
        (chat, key),
    )

    row = cursor.fetchone()

    if row:
        await update.message.reply_text(row[0])
