from app.db import conn
from app.messages import ACCESS_DENIED
from app.runtime import is_admin


async def audit(update, context):
    if not await is_admin(update, context):
        await update.message.reply_text(ACCESS_DENIED)
        return

    chat = update.effective_chat.id
    cursor = conn.cursor()

    if context.args:
        cursor.execute(
            """
            SELECT action,target,user_id,created_at
            FROM audit_log
            WHERE chat_id=%s AND target=%s
            ORDER BY created_at DESC
            LIMIT 10
            """,
            (chat, context.args[0]),
        )
    else:
        cursor.execute(
            """
            SELECT action,target,user_id,created_at
            FROM audit_log
            WHERE chat_id=%s
            ORDER BY created_at DESC
            LIMIT 10
            """,
            (chat,),
        )

    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("No audit entries found")
        return

    msg = "Audit log:\n\n"
    for action, target, user_id, created_at in rows:
        label = f" {target}" if target else ""
        msg += f"{created_at} - {action}{label} by {user_id}\n"

    await update.message.reply_text(msg)
