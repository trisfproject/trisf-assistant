async def resolve_username(context, username):
    if not username.startswith("@"):
        username = f"@{username}"

    try:
        chat = await context.bot.get_chat(username)
    except Exception:
        return None

    if getattr(chat, "type", None) != "private":
        return None

    return chat


def escape_markdown(value):
    text = str(value)
    for char in ("\\", "_", "*", "`", "["):
        text = text.replace(char, f"\\{char}")

    return text


def format_user_info(target_user):
    username = target_user.username
    username_text = escape_markdown(f"@{username}") if username else "-"
    name = getattr(target_user, "full_name", None) or getattr(target_user, "title", None) or "-"
    is_bot = str(getattr(target_user, "is_bot", False)).lower()

    return (
        "👤 User info\n\n"
        f"id: `{target_user.id}`\n"
        f"username: {username_text}\n"
        f"name: {escape_markdown(name)}\n"
        f"is_bot: {is_bot}"
    )


async def show_id(update, context):
    target_user = update.effective_user

    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    elif context.args and context.args[0].startswith("@"):
        target_user = await resolve_username(context, context.args[0])

        if not target_user:
            await update.message.reply_text("⚠️ User not found")
            return

    await update.message.reply_text(
        format_user_info(target_user),
        parse_mode="Markdown",
    )
