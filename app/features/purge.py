from datetime import datetime, timedelta, timezone

from telegram import Update
from telegram.ext import ContextTypes


async def is_group_admin(update, context):
    member = await context.bot.get_chat_member(
        update.effective_chat.id,
        update.effective_user.id,
    )

    return member.status in ["administrator", "creator"]


async def purge_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.message

    if chat.type == "private":
        await message.reply_text(
            "⚠️ This command only works in groups."
        )
        return

    if not await is_group_admin(update, context):
        await message.reply_text(
            "⛔ Only admins can purge messages."
        )
        return

    if not message.reply_to_message:
        await message.reply_text(
            "⚠️ Reply to the oldest message you want to purge."
        )
        return

    start_msg = message.reply_to_message

    now = datetime.now(timezone.utc)

    if now - start_msg.date > timedelta(hours=24):
        await message.reply_text(
            "⚠️ Cannot purge messages older than 24 hours."
        )
        return

    start_id = start_msg.message_id
    end_id = message.message_id

    total = end_id - start_id

    if total > 200:
        await message.reply_text(
            "⚠️ Purge limit exceeded (max 200 messages)."
        )
        return

    for msg_id in range(start_id, end_id + 1):
        try:
            await context.bot.delete_message(chat.id, msg_id)
        except Exception:
            pass

    try:
        await context.bot.delete_message(chat.id, message.message_id)
    except Exception:
        pass
