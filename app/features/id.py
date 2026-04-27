import html


def format_user_info(target_user):
    username = target_user.username
    username_text = f"@{username}" if username else "none"
    name = target_user.full_name or "none"
    is_bot = str(target_user.is_bot).lower()

    return (
        "👤 User info\n\n"
        f"id: <code>{target_user.id}</code>\n"
        f"username: {html.escape(username_text)}\n"
        f"name: {html.escape(name)}\n"
        f"is_bot: {is_bot}"
    )


def mentioned_user(message):
    text = message.text or message.caption or ""
    entities = message.entities or message.caption_entities or []

    for entity in entities:
        if entity.type == "text_mention" and entity.user:
            return entity.user

        if entity.type == "mention":
            username = text[entity.offset:entity.offset + entity.length].lstrip("@")
            if username:
                continue

    return None


async def show_id(update, context):
    target_user = update.effective_user

    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    else:
        target_user = mentioned_user(update.message) or target_user

    await update.message.reply_text(
        format_user_info(target_user),
        parse_mode="HTML",
    )
