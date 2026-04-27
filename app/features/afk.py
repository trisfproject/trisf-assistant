import datetime
import logging

from app.db import conn
from app.runtime import check_group, is_restricted_mode_blocked

logger = logging.getLogger(__name__)


def format_since(since):
    if not since:
        return "unknown time"

    delta = datetime.datetime.now() - since
    minutes = int(delta.total_seconds() // 60)

    if minutes < 1:
        return "just now"
    if minutes == 1:
        return "1 minute ago"

    return f"{minutes} minutes ago"


def display_user(user):
    if user.username:
        return f"@{user.username}"
    return user.full_name or str(user.id)


async def get_afk_status(chat, user):
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT reason,since
        FROM afk_status
        WHERE chat_id=%s AND user_id=%s
        """,
        (chat, user),
    )

    return cursor.fetchone()


async def get_mentioned_afk_users(update, context):
    message = update.message
    chat = update.effective_chat.id
    text = message.text or message.caption or ""
    entities = message.entities or message.caption_entities or []
    mentioned = {}

    if message.reply_to_message and message.reply_to_message.from_user:
        user = message.reply_to_message.from_user
        if user.id != update.effective_user.id:
            mentioned[user.id] = user

    for entity in entities:
        if entity.type == "text_mention" and entity.user:
            if entity.user.id != update.effective_user.id:
                mentioned[entity.user.id] = entity.user

        elif entity.type == "mention":
            username = text[entity.offset:entity.offset + entity.length].lstrip("@").lower()
            if not username:
                continue

            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT user_id
                FROM afk_status
                WHERE chat_id=%s
                """,
                (chat,),
            )

            for row in cursor.fetchall():
                try:
                    member = await context.bot.get_chat_member(chat, row[0])
                except Exception:
                    logger.exception("failed to inspect AFK mention user_id=%s", row[0])
                    continue

                user = member.user
                if user.username and user.username.lower() == username:
                    if user.id != update.effective_user.id:
                        mentioned[user.id] = user
                    break

    return mentioned


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


async def afk_watcher(update, context):
    if not update.message or not update.effective_user:
        return

    if update.message.text and update.message.text.startswith("/afk"):
        return

    chat = update.effective_chat.id
    user = update.effective_user.id

    if is_restricted_mode_blocked(chat, user):
        return

    current_status = await get_afk_status(chat, user)
    if current_status:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM afk_status
            WHERE chat_id=%s AND user_id=%s
            """,
            (chat, user),
        )
        await update.message.reply_text(
            f"{display_user(update.effective_user)} is back"
        )

    mentioned = await get_mentioned_afk_users(update, context)

    for mentioned_user_id, mentioned_user in mentioned.items():
        row = await get_afk_status(chat, mentioned_user_id)
        if not row:
            continue

        reason, since = row
        await update.message.reply_text(
            f"{display_user(mentioned_user)} is AFK: {reason} (since {format_since(since)})"
        )
