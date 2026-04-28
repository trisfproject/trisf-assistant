from telegram import Update
from telegram.ext import ContextTypes

from app.features.approvals import is_approved_user
from app.runtime import is_admin


def _command_body(message_text):
    if not message_text:
        return ""

    parts = message_text.split(maxsplit=1)
    if len(parts) < 2:
        return ""

    return parts[1].strip()


async def ghost_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user = update.effective_user
    chat = update.effective_chat

    if not message or not user or not chat:
        return

    if (
        not await is_admin(update, context)
        and not is_approved_user(user.id, chat.id)
    ):
        await message.reply_text(
            "❌ You are not allowed to use ghost relay mode."
        )
        return

    ghost_text = None

    if message.reply_to_message:
        if context.args:
            ghost_text = " ".join(context.args)
        else:
            ghost_text = message.reply_to_message.text
    else:
        ghost_text = _command_body(message.text or message.caption)

        if not ghost_text:
            await message.reply_text(
                "⚠️ Usage:\n/ghost <message>\nor reply message with /ghost"
            )
            return

    if not ghost_text:
        await message.reply_text(
            "⚠️ Could not read replied message text."
        )
        return

    try:
        await message.delete()
    except Exception:
        await message.reply_text(
            "⚠️ I need delete message permission to use ghost mode."
        )
        return

    await context.bot.send_message(
        chat_id=chat.id,
        text=ghost_text,
        reply_to_message_id=(
            message.reply_to_message.message_id
            if message.reply_to_message
            else None
        ),
        message_thread_id=message.message_thread_id,
        disable_notification=True,
    )
