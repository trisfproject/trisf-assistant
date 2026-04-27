from app.db import conn
from app.messages import WRITE_DENIED
from app.permissions import is_writer
from app.runtime import check_group


def ensure_todo_schema():
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS todos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            chat_id BIGINT,
            task TEXT,
            created_by BIGINT,
            completed BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA=DATABASE()
        AND TABLE_NAME='todos'
        """
    )

    columns = {row[0] for row in cursor.fetchall()}

    if "completed" not in columns:
        cursor.execute(
            """
            ALTER TABLE todos
            ADD COLUMN completed BOOLEAN DEFAULT FALSE
            """
        )

        if "is_done" in columns:
            cursor.execute(
                """
                UPDATE todos
                SET completed=is_done
                """
            )


async def list_todos(update, chat):
    ensure_todo_schema()

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT task,completed
        FROM todos
        WHERE chat_id=%s
        ORDER BY completed,id
        """,
        (chat,),
    )

    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("No todos.")
        return

    msg = "Todos:\n\n"
    for task, completed in rows:
        prefix = "✔" if completed else "•"
        msg += f"{prefix} {task}\n"

    await update.message.reply_text(msg)


async def add_todo(update, chat, user, task):
    if not task:
        await update.message.reply_text("usage: /todo add item")
        return

    if not is_writer(chat, user):
        await update.message.reply_text(WRITE_DENIED)
        return

    ensure_todo_schema()

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO todos (chat_id,task,created_by)
        VALUES (%s,%s,%s)
        """,
        (chat, task, user),
    )

    await update.message.reply_text("✅ todo added")


async def complete_todo(update, chat, user, todo_id):
    if not is_writer(chat, user):
        await update.message.reply_text(WRITE_DENIED)
        return

    ensure_todo_schema()

    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE todos
        SET completed=TRUE
        WHERE id=%s AND chat_id=%s
        """,
        (todo_id, chat),
    )

    if cursor.rowcount == 0:
        await update.message.reply_text("Todo not found.")
        return

    await update.message.reply_text("✅ todo completed")


async def delete_todo(update, chat, user, todo_id):
    if not is_writer(chat, user):
        await update.message.reply_text(WRITE_DENIED)
        return

    ensure_todo_schema()

    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM todos
        WHERE id=%s AND chat_id=%s
        """,
        (todo_id, chat),
    )

    if cursor.rowcount == 0:
        await update.message.reply_text("Todo not found.")
        return

    await update.message.reply_text("🗑 todo deleted")


async def todo(update, context):
    if not await check_group(update):
        return

    chat = update.effective_chat.id
    user = update.effective_user.id

    if not context.args:
        await list_todos(update, chat)
        return

    command = context.args[0].lower()

    if command == "list":
        await list_todos(update, chat)
        return

    if command == "add":
        await add_todo(update, chat, user, " ".join(context.args[1:]))
        return

    if command in ("done", "complete"):
        if len(context.args) < 2 or not context.args[1].isdigit():
            await update.message.reply_text("usage: /todo done 1")
            return

        await complete_todo(update, chat, user, int(context.args[1]))
        return

    if command == "delete":
        if len(context.args) < 2 or not context.args[1].isdigit():
            await update.message.reply_text("usage: /todo delete 1")
            return

        await delete_todo(update, chat, user, int(context.args[1]))
        return

    await add_todo(update, chat, user, " ".join(context.args))
