from telegram import Update
from telegram.ext import ContextTypes


async def is_telegram_group_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if not chat or not user or chat.type == "private":
        return False

    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
    except Exception:
        return False

    return member.status in ("administrator", "creator")


async def resolve_target_user(update, context):
    if update.message.reply_to_message:
        return update.message.reply_to_message.from_user

    if context.args:
        username = context.args[0].replace("@", "")
        members = await context.bot.get_chat_administrators(
            update.effective_chat.id
        )

        for admin in members:
            if admin.user.username == username:
                return admin.user

    return None


async def promote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    if chat.type == "private":
        await update.message.reply_text(
            "⚠️ This command only works in groups."
        )
        return

    if not await is_telegram_group_admin(update, context):
        await update.message.reply_text(
            "⛔ Only Telegram group admins can promote users."
        )
        return

    target = await resolve_target_user(update, context)

    if target is None:
        await update.message.reply_text(
            "⚠️ Reply to a user or provide a username."
        )
        return

    try:
        await context.bot.promote_chat_member(
            chat_id=chat.id,
            user_id=target.id,
            can_change_info=False,
            can_delete_messages=True,
            can_invite_users=True,
            can_pin_messages=True,
            can_manage_topics=True,
            can_promote_members=False,
        )

        await update.message.reply_text(
            f"✅ {target.full_name} promoted as group admin."
        )

    except Exception as e:
        if "ChatAdminRequired" in str(e):
            await update.message.reply_text(
                "⚠️ I need admin permission with 'Add new admins'."
            )
        else:
            await update.message.reply_text(
                "❌ Failed to promote user."
            )


async def demote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    if chat.type == "private":
        await update.message.reply_text(
            "⚠️ This command only works in groups."
        )
        return

    if not await is_telegram_group_admin(update, context):
        await update.message.reply_text(
            "⛔ Only Telegram group admins can demote users."
        )
        return

    target = await resolve_target_user(update, context)

    if target is None:
        await update.message.reply_text(
            "⚠️ Reply to a user or provide a username."
        )
        return

    try:
        await context.bot.promote_chat_member(
            chat_id=chat.id,
            user_id=target.id,
            can_change_info=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_pin_messages=False,
            can_manage_topics=False,
            can_promote_members=False,
        )

        await update.message.reply_text(
            f"⬇️ {target.full_name} removed from admin role."
        )

    except Exception as e:
        if "ChatAdminRequired" in str(e):
            await update.message.reply_text(
                "⚠️ I need admin permission with 'Add new admins'."
            )
        else:
            await update.message.reply_text(
                "❌ Failed to demote user."
            )


async def admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    if chat.type == "private":
        await update.message.reply_text(
            "⚠️ This command only works in groups."
        )
        return

    if not await is_telegram_group_admin(update, context):
        await update.message.reply_text(
            "⛔ Only Telegram group admins can view admin list."
        )
        return

    admins = await context.bot.get_chat_administrators(chat.id)

    admin_list = []

    for admin in admins:
        user = admin.user
        name = user.full_name

        if user.username:
            name += f" (@{user.username})"

        admin_list.append(f"• {name}")

    if not admin_list:
        await update.message.reply_text(
            "⚠️ No admins found."
        )
        return

    text = "👮 Group admins:\n\n" + "\n".join(admin_list)

    await update.message.reply_text(text)
