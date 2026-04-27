import html

from telegram import MessageEntity


async def show_id(update, context):
    message = update.message
    chat = update.effective_chat

    if not message:
        return

    target_user = None

    # PRIORITY 1: reply target
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user

    # PRIORITY 2: TEXT_MENTION (clickable mention)
    elif message.entities:
        for entity in message.entities:
            if entity.type == MessageEntity.TEXT_MENTION:
                target_user = entity.user
                break

    # PRIORITY 3: username mention (@username)
    if not target_user and message.entities:
        for entity in message.entities:
            if entity.type == MessageEntity.MENTION:
                username = message.text[
                    entity.offset : entity.offset + entity.length
                ].replace("@", "")

                try:
                    admins = await context.bot.get_chat_administrators(chat.id)

                    for admin in admins:
                        if admin.user.username == username:
                            target_user = admin.user
                            break

                except Exception:
                    pass

    # PRIORITY 4: fallback self
    if not target_user:
        target_user = update.effective_user

    username = (
        f"@{target_user.username}"
        if target_user.username
        else "none"
    )
    name = target_user.full_name or "none"

    text = (
        "👤 User info\n\n"
        f"id: <code>{target_user.id}</code>\n"
        f"username: {html.escape(username)}\n"
        f"name: {html.escape(name)}\n"
        f"is_bot: {str(target_user.is_bot).lower()}"
    )

    await message.reply_text(
        text,
        parse_mode="HTML",
    )
