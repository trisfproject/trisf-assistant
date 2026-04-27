from telegram import Update
from telegram.ext import ContextTypes

from app.permissions import is_superuser, is_writer


async def can_pin(context, chat_id, user_id):
    if is_superuser(user_id) or is_writer(chat_id, user_id):
        return True

    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
    except Exception:
        return False

    return member.status in ("administrator", "creator")


async def pin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat = update.effective_chat

    if not message or not chat or not update.effective_user:
        return

    user_id = update.effective_user.id

    if chat.type == "private":
        await message.reply_text(
            "⚠️ Pin is only available in groups."
        )
        return

    if not message.reply_to_message:
        await message.reply_text(
            "⚠️ Reply to a message to pin it."
        )
        return

    if not await can_pin(context, chat.id, user_id):
        await message.reply_text(
            "⛔ You don't have permission to pin messages."
        )
        return

    try:
        await context.bot.pin_chat_message(
            chat_id=chat.id,
            message_id=message.reply_to_message.message_id,
            disable_notification=False,
        )

        await message.reply_text(
            "📌 Message pinned"
        )

    except Exception as e:
        if "ChatAdminRequired" in str(e):
            await message.reply_text(
                "⚠️ I need admin permission to pin messages in this chat."
            )
        else:
            await message.reply_text(
                "❌ Failed to pin message."
            )


async def unpin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat = update.effective_chat

    if not message or not chat or not update.effective_user:
        return

    user_id = update.effective_user.id

    if chat.type == "private":
        await message.reply_text(
            "⚠️ Pin is only available in groups."
        )
        return

    if not message.reply_to_message:
        await message.reply_text(
            "⚠️ Reply to a pinned message to unpin it."
        )
        return

    if not await can_pin(context, chat.id, user_id):
        await message.reply_text(
            "⛔ You don't have permission to unpin messages."
        )
        return

    try:
        await context.bot.unpin_chat_message(
            chat_id=chat.id,
            message_id=message.reply_to_message.message_id,
        )

        await message.reply_text(
            "📌 Message unpinned"
        )

    except Exception as e:
        if "ChatAdminRequired" in str(e):
            await message.reply_text(
                "⚠️ I need admin permission to unpin messages in this chat."
            )
        else:
            await message.reply_text(
                "❌ Failed to unpin message."
            )
