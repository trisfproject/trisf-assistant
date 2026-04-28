from telegram import Update
from telegram.ext import ContextTypes


async def is_group_admin(update, context):
    member = await context.bot.get_chat_member(
        update.effective_chat.id,
        update.effective_user.id,
    )

    return member.status in ["administrator", "creator"]


async def resolve_target_user(update, context):
    if update.message.reply_to_message:
        return update.message.reply_to_message.from_user

    if context.args:
        username = context.args[0].replace("@", "")

        members = await context.bot.get_chat_administrators(
            update.effective_chat.id
        )

        for member in members:
            if member.user.username == username:
                return member.user

    return None


async def resolve_target_user_id(update, context):
    target = await resolve_target_user(update, context)

    if target:
        return target.id, target.full_name

    if context.args:
        value = context.args[0].replace("@", "")

        if value.isdigit():
            return int(value), value

    return None, None


async def kick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    if chat.type == "private":
        await update.message.reply_text(
            "⚠️ This command only works in groups."
        )
        return

    if not await is_group_admin(update, context):
        await update.message.reply_text(
            "⛔ Only admins can remove users."
        )
        return

    target = await resolve_target_user(update, context)

    if not target:
        await update.message.reply_text(
            "⚠️ Reply to a user to remove them."
        )
        return

    member = await context.bot.get_chat_member(
        chat.id,
        target.id,
    )

    if member.status == "creator":
        await update.message.reply_text(
            "⚠️ Cannot remove group owner."
        )
        return

    if target.id == context.bot.id:
        await update.message.reply_text(
            "⚠️ I cannot remove myself."
        )
        return

    try:
        await context.bot.ban_chat_member(
            chat.id,
            target.id,
        )

        await context.bot.unban_chat_member(
            chat.id,
            target.id,
        )

        await update.message.reply_text(
            f"👢 {target.full_name} removed from group."
        )
    except Exception:
        await update.message.reply_text(
            "⚠️ I need permission: Ban users."
        )


async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    if chat.type == "private":
        await update.message.reply_text(
            "⚠️ This command only works in groups."
        )
        return

    if not await is_group_admin(update, context):
        await update.message.reply_text(
            "⛔ Only admins can ban users."
        )
        return

    target = await resolve_target_user(update, context)

    if not target:
        await update.message.reply_text(
            "⚠️ Reply to a user to ban them."
        )
        return

    member = await context.bot.get_chat_member(
        chat.id,
        target.id,
    )

    if member.status == "creator":
        await update.message.reply_text(
            "⚠️ Cannot ban group owner."
        )
        return

    if target.id == context.bot.id:
        await update.message.reply_text(
            "⚠️ I cannot ban myself."
        )
        return

    try:
        await context.bot.ban_chat_member(
            chat.id,
            target.id,
        )

        await update.message.reply_text(
            f"🚫 {target.full_name} banned from group."
        )
    except Exception:
        await update.message.reply_text(
            "⚠️ I need permission: Ban users."
        )


async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    if chat.type == "private":
        await update.message.reply_text(
            "⚠️ This command only works in groups."
        )
        return

    if not await is_group_admin(update, context):
        await update.message.reply_text(
            "⛔ Only admins can unban users."
        )
        return

    target_id, target_name = await resolve_target_user_id(update, context)

    if not target_id:
        await update.message.reply_text(
            "📘 Usage: /unban <user_id>"
        )
        return

    try:
        await context.bot.unban_chat_member(
            chat.id,
            target_id,
        )

        await update.message.reply_text(
            f"✅ {target_name} unbanned."
        )
    except Exception:
        await update.message.reply_text(
            "⚠️ Failed to unban user."
        )
