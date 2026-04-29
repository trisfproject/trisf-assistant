from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes


AFK_USERS = {}


def format_duration(seconds):
    minutes = seconds // 60

    if minutes < 1:
        return f"{seconds}s"

    if minutes < 60:
        return f"{minutes} minutes"

    hours = minutes // 60
    return f"{hours} hours"


async def afk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    reason = " ".join(context.args) if context.args else "AFK"

    AFK_USERS[user.id] = {
        "reason": reason,
        "since": datetime.utcnow(),
        "first_name": user.first_name,
        "username": user.username.lower() if user.username else None,
    }

    await update.message.reply_text(
        f"😴 AFK mode enabled\n"
        f"📝 Reason: {reason}"
    )


async def afk_check_mentions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    sender = update.effective_user

    if not message:
        return

    notified_users = set()

    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user

        if target_user.id in AFK_USERS and (not sender or target_user.id != sender.id):
            await _reply_with_afk_status(message, target_user.id, target_user.first_name)
            notified_users.add(target_user.id)

    text = message.text or message.caption or ""
    entities = message.entities or message.caption_entities or []

    for entity in entities:
        target_user_id = None
        target_name = None

        if entity.type == "text_mention" and entity.user:
            target_user_id = entity.user.id
            target_name = entity.user.first_name

        elif entity.type == "mention":
            username = text[entity.offset:entity.offset + entity.length].lstrip("@").lower()

            if context.bot.username and username == context.bot.username.lower():
                continue

            for uid, data in AFK_USERS.items():
                if data.get("username") == username:
                    target_user_id = uid
                    target_name = data.get("first_name")
                    break

        if (
            target_user_id in AFK_USERS
            and target_user_id not in notified_users
            and (not sender or target_user_id != sender.id)
        ):
            await _reply_with_afk_status(message, target_user_id, target_name)
            notified_users.add(target_user_id)


async def afk_auto_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message

    if not user or not message:
        return

    if message.text and message.text.startswith("/afk"):
        return

    if user.id in AFK_USERS:
        afk_data = AFK_USERS.pop(user.id)
        duration = datetime.utcnow() - afk_data["since"]
        seconds = int(duration.total_seconds())
        formatted = format_duration(seconds)

        await message.reply_text(
            f"👋 Welcome back!\n"
            f"⏱ AFK duration: {formatted}"
        )


async def _reply_with_afk_status(message, user_id, first_name):
    afk_data = AFK_USERS[user_id]
    duration = datetime.utcnow() - afk_data["since"]
    seconds = int(duration.total_seconds())
    formatted = format_duration(seconds)
    display_name = first_name or afk_data.get("first_name") or "User"

    await message.reply_text(
        f"👤 {display_name} is currently AFK\n"
        f"📝 Reason: {afk_data['reason']}\n"
        f"⏱ AFK since: {formatted}"
    )
