def escape_markdown(value):
    text = str(value)
    for char in ("\\", "_", "*", "`", "["):
        text = text.replace(char, f"\\{char}")

    return text


async def chatid(update, context):
    chat = update.effective_chat
    thread_id = update.message.message_thread_id

    if thread_id:
        text = (
            "🧵 Topic info\n\n"
            f"chat_id: `{chat.id}`\n"
            f"thread_id: `{thread_id}`\n"
            f"type: {escape_markdown(chat.type)}"
        )
    elif chat.type == "private":
        text = (
            "👤 Chat info\n\n"
            f"chat_id: `{chat.id}`\n"
            f"type: {escape_markdown(chat.type)}"
        )
    else:
        title = chat.title or "none"
        text = (
            "👥 Chat info\n\n"
            f"chat_id: `{chat.id}`\n"
            f"type: {escape_markdown(chat.type)}\n"
            f"title: {escape_markdown(title)}"
        )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
    )
