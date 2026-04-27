from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from app.permissions import is_superuser


async def can_view_admin(context, chat_id, user_id):
    if is_superuser(user_id):
        return True

    if chat_id is None:
        return False

    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
    except Exception:
        return False

    return member.status in ("administrator", "creator")


def build_help_keyboard(show_admin=False):
    keyboard = [
        [
            InlineKeyboardButton("📌 Notes", callback_data="help_notes"),
            InlineKeyboardButton("📋 Tasks", callback_data="help_tasks"),
        ],
        [
            InlineKeyboardButton("📍 Messages", callback_data="help_messages"),
            InlineKeyboardButton("⏰ Reminders", callback_data="help_reminders"),
        ],
        [
            InlineKeyboardButton("🌐 Network", callback_data="help_network"),
            InlineKeyboardButton("👤 Info", callback_data="help_info"),
        ],
    ]

    channel_button = InlineKeyboardButton(
        "📢 Channel",
        url="https://t.me/trisfproject",
    )

    if show_admin:
        keyboard.append(
            [
                InlineKeyboardButton("🔐 Admin", callback_data="help_admin"),
                channel_button,
            ]
        )
    else:
        keyboard.append([channel_button])

    keyboard.append([InlineKeyboardButton("✅ Done", callback_data="help_done")])

    return keyboard


def submenu_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅ Back",
                    callback_data="help_back",
                ),
                InlineKeyboardButton(
                    "✅ Done",
                    callback_data="help_done",
                ),
            ]
        ]
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id if update.effective_chat else None
    show_admin = await can_view_admin(context, chat_id, user_id)
    keyboard = build_help_keyboard(show_admin)

    await update.message.reply_text(
        "🤖 trisf assistant\n\nWhat do you want to check?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def help_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id
    chat_id = query.message.chat.id if query.message and query.message.chat else None
    show_admin = await can_view_admin(context, chat_id, user_id)

    if data == "help_done":
        try:
            await query.delete_message()
        except Exception:
            await query.edit_message_text("✅ Done")
        return

    if data == "help_back":
        keyboard = build_help_keyboard(show_admin)
        await query.edit_message_text(
            "🤖 trisf assistant\n\nWhat do you want to check?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    if data == "help_notes":
        text = (
            "📌 Notes\n\n"
            "#<key>\n"
            "/save <key> (approved only)"
        )
        await query.edit_message_text(
            text,
            reply_markup=submenu_keyboard(),
        )
        return

    if data == "help_tasks":
        text = (
            "📋 Tasks\n\n"
            "/todo\n"
            "/todo done <id>\n"
            "/todo add <text> (approved only)\n"
            "/todo delete <id> (approved only)"
        )

        await query.edit_message_text(
            text,
            reply_markup=submenu_keyboard(),
        )
        return

    if data == "help_messages":
        await query.edit_message_text(
            "📍 Messages\n\n"
            "/pin\nReply to a message to pin it\n\n"
            "/unpin\nReply to a pinned message to unpin it\n\n"
            "/afk <reason>\n"
            "Mark yourself as away.\n"
            "The bot notifies others when they mention or reply to you.",
            reply_markup=submenu_keyboard(),
        )
        return

    if data == "help_reminders":
        await query.edit_message_text(
            "⏰ Reminders\n\n"
            "/remind <time> <text>",
            reply_markup=submenu_keyboard(),
        )
        return

    if data == "help_network":
        await query.edit_message_text(
            "🌐 Network tools\n\n"
            "/ping <host>\n"
            "/dns <domain> [type]\n"
            "/http <url>\n"
            "/whois <domain|ip>",
            reply_markup=submenu_keyboard(),
        )
        return

    if data == "help_info":
        await query.edit_message_text(
            "👤 Info\n\n"
            "/id\n"
            "Show your Telegram user ID.\n"
            "Reply to a user message to show their ID.\n\n"
            "/chatid\n"
            "Show current chat ID and type.\n"
            "In forum topics, also shows thread ID.",
            reply_markup=submenu_keyboard(),
        )
        return

    if data == "help_admin":
        if show_admin:
            text = (
                "🔐 Admin tools\n\n"
                "/approvelist\n"
                "Show approved users in this group.\n\n"
                "/audit\n"
                "Show recent audit log entries.\n\n"
                "/audit <target>\n"
                "Filter audit entries by target.\n\n"
                "/export\n"
                "Create a backup export.\n\n"
                "/import\n"
                "Restore data from a backup JSON file."
            )
        else:
            text = (
                "🔐 Admin tools\n\n"
                "Admin menu is available to group admins, owners, and superusers."
            )

        await query.edit_message_text(
            text,
            reply_markup=submenu_keyboard(),
        )
        return
