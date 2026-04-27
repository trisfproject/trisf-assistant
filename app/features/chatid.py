async def chatid(update, context):

    message = update.message
    chat = update.effective_chat

    if not message:
        return

    thread_id = message.message_thread_id

    try:

        if chat.type == "private":

            text = (
                "👤 Chat info\n\n"
                f"chat_id: `{chat.id}`\n"
                f"type: {chat.type}"
            )

        elif thread_id:

            text = (
                "🧵 Topic info\n\n"
                f"chat_id: `{chat.id}`\n"
                f"thread_id: `{thread_id}`\n"
                f"type: {chat.type}"
            )

        else:

            title = chat.title or "none"

            text = (
                "👥 Chat info\n\n"
                f"chat_id: `{chat.id}`\n"
                f"type: {chat.type}\n"
                f"title: {title}"
            )

        print("chatid handler triggered")
        await message.reply_text(text, parse_mode="Markdown")

    except Exception as e:

        await message.reply_text(f"chatid error: {e}")
