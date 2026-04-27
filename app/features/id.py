import html

from telegram import MessageEntity


def mentioned_username(message):
    text = message.text or message.caption or ""
    entities = message.entities or message.caption_entities or []

    for entity in entities:
        if entity.type == MessageEntity.MENTION:
            return text[
                entity.offset : entity.offset + entity.length
            ].replace("@", "").lower()

    return None


async def show_id(update, context):
    message = update.message

    if not message:
        return

    target_user = None

    if mentioned_username(message):
        await message.reply_text(
            "⚠️ Username lookup is not supported.\nReply to a user message and send /id instead."
        )
        return

    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif message.entities:
        for entity in message.entities:
            if entity.type == MessageEntity.TEXT_MENTION:
                target_user = entity.user
                break

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
