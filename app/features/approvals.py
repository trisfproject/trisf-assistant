from app.db import conn
from app.messages import ACCESS_DENIED
from app.runtime import is_admin, log_action


async def approve(update, context):

    if not await is_admin(update, context):
        await update.message.reply_text(ACCESS_DENIED)
        return

    chat = update.effective_chat.id

    if update.message.reply_to_message:

        user = update.message.reply_to_message.from_user

        uid = user.id
        username = user.username
        fullname = user.full_name

    else:

        if not context.args:
            return

        uid = int(context.args[0])
        username = None
        fullname = None

    cursor = conn.cursor()

    cursor.execute(
        """
        REPLACE INTO approved_users
        (chat_id,user_id,username,full_name)
        VALUES (%s,%s,%s,%s)
        """,
        (chat, uid, username, fullname),
    )

    log_action(chat, update.effective_user.id, "approve", uid)

    await update.message.reply_text("✅ user approved")


async def revoke(update, context):

    if not await is_admin(update, context):
        await update.message.reply_text(ACCESS_DENIED)
        return

    chat = update.effective_chat.id

    if not context.args:
        return

    uid = int(context.args[0])

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM approved_users
        WHERE chat_id=%s AND user_id=%s
        """,
        (chat, uid),
    )

    log_action(chat, update.effective_user.id, "revoke", uid)

    await update.message.reply_text("🚫 access revoked")


async def approvelist(update, context):

    if not await is_admin(update, context):
        await update.message.reply_text(ACCESS_DENIED)
        return

    chat = update.effective_chat.id

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT username,full_name,user_id
        FROM approved_users
        WHERE chat_id=%s
        """,
        (chat,),
    )

    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text(
            "Belum ada user yang di-approve."
        )
        return

    msg = "Approved users:\n\n"

    for username, fullname, uid in rows:

        if username:
            msg += f"@{username}\n"
        elif fullname:
            msg += f"{fullname}\n"
        else:
            msg += f"{uid}\n"

    await update.message.reply_text(msg)
