from telegram import Update
from telegram.ext import CommandHandler, ContextTypes


async def resolve_target_user(update, context):
    if update.message.reply_to_message:
        return update.message.reply_to_message.from_user

    if context.args:
        username = context.args[0].replace("@", "")

        admins = await context.bot.get_chat_administrators(
            update.effective_chat.id
        )

        for admin in admins:
            if admin.user.username == username:
                return admin.user

    return None


async def is_group_admin(update, context):
    member = await context.bot.get_chat_member(
        update.effective_chat.id,
        update.effective_user.id,
    )

    return member.status in ["administrator", "creator"]


async def promote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    if chat.type != "supergroup":
        await update.message.reply_text(
            "⚠️ This command only works in supergroups."
        )
        return

    if not await is_group_admin(update, context):
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

    member = await context.bot.get_chat_member(
        chat.id,
        target.id,
    )

    if member.status in ["administrator", "creator"]:
        await update.message.reply_text(
            "⚠️ User already admin"
        )
        return

    try:
        bot_member = await context.bot.get_chat_member(
            chat.id,
            context.bot.id,
        )

        await context.bot.promote_chat_member(
            chat_id=chat.id,
            user_id=target.id,
            can_delete_messages=bot_member.can_delete_messages,
            can_restrict_members=bot_member.can_restrict_members,
            can_invite_users=bot_member.can_invite_users,
            can_manage_video_chats=getattr(
                bot_member,
                "can_manage_video_chats",
                False,
            ),
            can_manage_topics=getattr(
                bot_member,
                "can_manage_topics",
                False,
            ),
            can_post_stories=False,
            can_edit_stories=False,
            can_delete_stories=False,
            can_change_info=False,
            can_pin_messages=False,
            can_promote_members=False,
            is_anonymous=False,
        )

        await update.message.reply_text(
            "✅ User promoted as moderator"
        )

    except Exception as e:
        if "ChatAdminRequired" in str(e):
            await update.message.reply_text(
                "⚠️ I need permission: Add new admins."
            )
        else:
            await update.message.reply_text(
                "❌ Failed to promote user."
            )


async def demote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    if chat.type != "supergroup":
        await update.message.reply_text(
            "⚠️ This command only works in supergroups."
        )
        return

    if not await is_group_admin(update, context):
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

    member = await context.bot.get_chat_member(
        chat.id,
        target.id,
    )

    if member.status not in ["administrator", "creator"]:
        await update.message.reply_text(
            "⚠️ This user is not an admin."
        )
        return

    try:
        await context.bot.promote_chat_member(
            chat_id=chat.id,
            user_id=target.id,
            can_manage_chat=False,
            can_delete_messages=False,
            can_restrict_members=False,
            can_invite_users=False,
            can_manage_video_chats=False,
            can_manage_topics=False,
            can_post_stories=False,
            can_edit_stories=False,
            can_delete_stories=False,
            can_change_info=False,
            can_pin_messages=False,
            can_promote_members=False,
            is_anonymous=False,
        )

        await update.message.reply_text(
            f"⬇️ {target.full_name} removed from admin role."
        )

    except Exception as e:
        if "ChatAdminRequired" in str(e):
            await update.message.reply_text(
                "⚠️ I need permission: Add new admins."
            )
        else:
            await update.message.reply_text(
                "❌ Failed to demote user."
            )


async def admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    if chat.type != "supergroup":
        await update.message.reply_text(
            "⚠️ This command only works in supergroups."
        )
        return

    if not await is_group_admin(update, context):
        await update.message.reply_text(
            "⛔ Only Telegram group admins can view admin list."
        )
        return

    admins = await context.bot.get_chat_administrators(chat.id)

    result = []

    for admin in admins:
        user = admin.user
        name = user.full_name

        if user.username:
            name += f" (@{user.username})"

        result.append(f"• {name}")

    text = "👮 Group admins:\n\n" + "\n".join(result)

    await update.message.reply_text(text)
