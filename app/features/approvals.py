from app.db import conn
from app.messages import ACCESS_DENIED
from app.runtime import is_admin, log_action


def is_approved_user(user_id, chat_id):
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT 1
        FROM approved_users
        WHERE chat_id=%s AND user_id=%s
        """,
        (chat_id, user_id),
    )

    return cursor.fetchone() is not None


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
            await update.message.reply_text(
                "📘 Usage:\n/approve user_id\nor reply to a message then run:\n/approve"
            )
            return

        if not context.args[0].isdigit():
            await update.message.reply_text(
                "📘 Usage:\n/approve user_id\nor reply to a message then run:\n/approve"
            )
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

    label = f"@{username}" if username else str(uid)
    await update.message.reply_text(f"👤 User approved: {label}")


async def revoke(update, context):

    if not await is_admin(update, context):
        await update.message.reply_text(ACCESS_DENIED)
        return

    chat = update.effective_chat.id
    uid = None
    username = None

    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        uid = user.id
        username = user.username

    elif context.args:
        target = context.args[0]

        if target.startswith("@"):
            username = target[1:]
        elif target.isdigit():
            uid = int(target)

    if uid is None and username is None:
        await update.message.reply_text(
            "📘 Usage:\n/revoke @username\nor reply to a message then run:\n/revoke"
        )
        return

    cursor = conn.cursor()

    if uid is not None:
        cursor.execute(
            """
            SELECT user_id,username
            FROM approved_users
            WHERE chat_id=%s AND user_id=%s
            """,
            (chat, uid),
        )
    else:
        cursor.execute(
            """
            SELECT user_id,username
            FROM approved_users
            WHERE chat_id=%s AND username=%s
            """,
            (chat, username),
        )

    row = cursor.fetchone()

    if not row:
        await update.message.reply_text("⚠️ User not found")
        return

    uid, stored_username = row

    cursor.execute(
        """
        DELETE FROM approved_users
        WHERE chat_id=%s AND user_id=%s
        """,
        (chat, uid),
    )

    log_action(chat, update.effective_user.id, "revoke", uid)

    label = f"@{stored_username}" if stored_username else str(uid)
    await update.message.reply_text(f"👤 User revoked: {label}")


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
            "👤 No approved users found"
        )
        return

    msg = "👤 Approved users:\n\n"

    for username, fullname, uid in rows:

        if username:
            msg += f"@{username}\n"
        elif fullname:
            msg += f"{fullname}\n"
        else:
            msg += f"{uid}\n"

    await update.message.reply_text(msg)
