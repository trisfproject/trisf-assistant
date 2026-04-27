from app.db import conn
from app.messages import WRITE_DENIED
from app.permissions import is_writer
from app.runtime import check_group


async def todo(update, context):
    if not await check_group(update):
        return

    chat = update.effective_chat.id
    user = update.effective_user.id

    if not context.args or context.args[0] == "list":
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id,task
            FROM todos
            WHERE chat_id=%s AND is_done=FALSE
            ORDER BY id
            """,
            (chat,),
        )

        rows = cursor.fetchall()

        if not rows:
            await update.message.reply_text("No open todos.")
            return

        msg = "Todos:\n\n"
        for row in rows:
            msg += f"{row[0]}. {row[1]}\n"

        await update.message.reply_text(msg)
        return

    if context.args[0] == "add":
        task = " ".join(context.args[1:])
    else:
        task = " ".join(context.args)

    if not task:
        await update.message.reply_text("usage: /todo add item")
        return

    if not is_writer(chat, user):
        await update.message.reply_text(WRITE_DENIED)
        return

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO todos (chat_id,task,created_by)
        VALUES (%s,%s,%s)
        """,
        (chat, task, user),
    )

    await update.message.reply_text("✅ todo added")
