from app.db import conn
from app.messages import WRITE_DENIED
from app.permissions import is_writer
from app.runtime import check_group


TODO_USAGE = "📘 Usage:\n/todo add text\n/todo done <id>\n/todo delete <id>"


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

    return columns


def parse_todo_id(value):
    value = value.lstrip("#")
    if not value.isdigit():
        return None

    return int(value)


def todo_scope(columns, chat, thread_id):
    where = ["chat_id=%s"]
    params = [chat]

    if thread_id and "message_thread_id" in columns:
        where.append("message_thread_id=%s")
        params.append(thread_id)

    return " AND ".join(where), params


async def list_todos(update, chat, thread_id):
    columns = ensure_todo_schema()
    where_sql, params = todo_scope(columns, chat, thread_id)

    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT id,task,completed
        FROM todos
        WHERE {where_sql}
        ORDER BY completed,id
        """,
        params,
    )

    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("📝 No todos found")
        return

    msg = "📝 Todo list\n\n"
    for todo_id, task, completed in rows:
        msg += f"#{todo_id} {task}\n"

    await update.message.reply_text(msg)


async def add_todo(update, chat, user, task, thread_id):
    if not task:
        await update.message.reply_text(TODO_USAGE)
        return

    if not is_writer(chat, user):
        await update.message.reply_text(WRITE_DENIED)
        return

    columns = ensure_todo_schema()

    cursor = conn.cursor()
    if thread_id and "message_thread_id" in columns:
        cursor.execute(
            """
            INSERT INTO todos (chat_id,task,created_by,message_thread_id)
            VALUES (%s,%s,%s,%s)
            """,
            (chat, task, user, thread_id),
        )
    else:
        cursor.execute(
            """
            INSERT INTO todos (chat_id,task,created_by)
            VALUES (%s,%s,%s)
            """,
            (chat, task, user),
        )

    await update.message.reply_text("📝 Todo added")


async def complete_todo(update, chat, user, todo_id, thread_id):
    if not is_writer(chat, user):
        await update.message.reply_text(WRITE_DENIED)
        return

    columns = ensure_todo_schema()
    where_sql, params = todo_scope(columns, chat, thread_id)

    cursor = conn.cursor()
    cursor.execute(
        f"""
        UPDATE todos
        SET completed=TRUE
        WHERE id=%s AND {where_sql}
        """,
        [todo_id] + params,
    )

    if cursor.rowcount == 0:
        await update.message.reply_text("⚠️ Todo not found")
        return

    await update.message.reply_text("✅ Todo completed")


async def delete_todo(update, chat, user, todo_id, thread_id):
    if not is_writer(chat, user):
        await update.message.reply_text(WRITE_DENIED)
        return

    columns = ensure_todo_schema()
    where_sql, params = todo_scope(columns, chat, thread_id)

    cursor = conn.cursor()
    cursor.execute(
        f"""
        DELETE FROM todos
        WHERE id=%s AND {where_sql}
        """,
        [todo_id] + params,
    )

    if cursor.rowcount == 0:
        await update.message.reply_text("⚠️ Todo not found")
        return

    await update.message.reply_text("✅ Todo removed")


async def todo(update, context):
    if not await check_group(update):
        return

    chat = update.effective_chat.id
    user = update.effective_user.id
    thread_id = update.message.message_thread_id

    if not context.args:
        await list_todos(update, chat, thread_id)
        return

    command = context.args[0].lower()

    if command == "list":
        await list_todos(update, chat, thread_id)
        return

    if command == "add":
        await add_todo(update, chat, user, " ".join(context.args[1:]), thread_id)
        return

    if command in ("done", "complete"):
        todo_id = parse_todo_id(context.args[1]) if len(context.args) >= 2 else None
        if todo_id is None:
            await update.message.reply_text(TODO_USAGE)
            return

        await complete_todo(update, chat, user, todo_id, thread_id)
        return

    if command == "delete":
        todo_id = parse_todo_id(context.args[1]) if len(context.args) >= 2 else None
        if todo_id is None:
            await update.message.reply_text(TODO_USAGE)
            return

        await delete_todo(update, chat, user, todo_id, thread_id)
        return

    await add_todo(update, chat, user, " ".join(context.args), thread_id)
