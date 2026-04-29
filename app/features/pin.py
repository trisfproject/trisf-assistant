import asyncio

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


async def delete_later(bot, chat_id, message_id):
    await asyncio.sleep(5)

    try:
        await bot.delete_message(chat_id, message_id)
    except Exception:
        pass


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
            "⚠️ Reply to a message first."
        )
        return

    if not await can_pin(context, chat.id, user_id):
        await message.reply_text(
            "⛔ You don't have permission to pin messages."
        )
        return

    notify_mode = False

    if context.args:
        if context.args[0].lower() == "loud":
            notify_mode = True

    pin_disable_notification = not notify_mode

    try:
        await chat.pin_message(
            message.reply_to_message.message_id,
            disable_notification=pin_disable_notification,
        )

    except Exception:
        await message.reply_text(
            "❌ I need pin permission to do that."
        )
        return

    try:
        await message.delete()
    except Exception:
        pass

    confirmation_text = (
        "📌 Message pinned (notification sent)"
        if notify_mode
        else "📌 Message pinned"
    )

    confirm = await chat.send_message(
        confirmation_text,
        disable_notification=not notify_mode,
    )

    asyncio.create_task(
        delete_later(
            context.bot,
            confirm.chat_id,
            confirm.message_id,
        )
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

    if not await can_pin(context, chat.id, user_id):
        await message.reply_text(
            "⛔ You don't have permission to unpin messages."
        )
        return

    notify_mode = False

    if context.args:
        if context.args[0].lower() == "loud":
            notify_mode = True

    try:
        await chat.unpin_all_messages()

    except Exception:
        await message.reply_text(
            "❌ I need pin permission to do that."
        )
        return

    try:
        await message.delete()
    except Exception:
        pass

    confirmation_text = (
        "📍 Message unpinned (notification sent)"
        if notify_mode
        else "📍 Message unpinned"
    )

    confirm = await chat.send_message(
        confirmation_text,
        disable_notification=not notify_mode,
    )

    asyncio.create_task(
        delete_later(
            context.bot,
            confirm.chat_id,
            confirm.message_id,
        )
    )
