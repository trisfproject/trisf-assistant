from telegram import Update
from telegram.ext import ContextTypes


async def is_group_admin(update, context):
    member = await context.bot.get_chat_member(
        update.effective_chat.id,
        update.effective_user.id,
    )

    return member.status in ["administrator", "creator"]


async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    if chat.type == "private":
        await update.message.reply_text(
            "⚠️ This command only works in groups."
        )
        return

    if not await is_group_admin(update, context):
        await update.message.reply_text(
            "⛔ Only admins can delete messages."
        )
        return

    if not update.message.reply_to_message:
        await update.message.reply_text(
            "⚠️ Reply to a message to delete it."
        )
        return

    try:
        await context.bot.delete_message(
            chat.id,
            update.message.reply_to_message.message_id,
        )

        await context.bot.delete_message(
            chat.id,
            update.message.message_id,
        )

    except Exception:
        await update.message.reply_text(
            "⚠️ I need permission: Delete messages"
        )
