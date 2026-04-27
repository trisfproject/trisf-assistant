import html

from telegram import MessageEntity


USER_CACHE_BY_CHAT = {}
USER_CACHE_GLOBAL = {}


def cache_user(chat_id, user):
    if not user or not user.username:
        return

    username = user.username.lower()
    USER_CACHE_BY_CHAT[(chat_id, username)] = user
    USER_CACHE_GLOBAL[username] = user


def cache_message_users(message, chat_id):
    cache_user(chat_id, message.from_user)

    if message.reply_to_message:
        cache_user(chat_id, message.reply_to_message.from_user)

    entities = message.entities or message.caption_entities or []
    for entity in entities:
        if entity.type == MessageEntity.TEXT_MENTION:
            cache_user(chat_id, entity.user)


async def remember_user(update, context):
    if not update.message or not update.effective_chat:
        return

    cache_message_users(update.message, update.effective_chat.id)


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
    chat = update.effective_chat

    if not message:
        return

    cache_message_users(message, chat.id)
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
        username = mentioned_username(message)

        if username:
            try:
                admins = await context.bot.get_chat_administrators(chat.id)

                for admin in admins:
                    if admin.user.username and admin.user.username.lower() == username:
                        target_user = admin.user
                        cache_user(chat.id, target_user)
                        break

            except Exception:
                pass

            if not target_user:
                target_user = (
                    USER_CACHE_BY_CHAT.get((chat.id, username))
                    or USER_CACHE_GLOBAL.get(username)
                )

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
