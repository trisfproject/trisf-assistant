from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from app.permissions import is_superuser, is_writer


def is_approved_user(chat_id, user_id):
    if chat_id is None:
        return False

    return is_writer(chat_id, user_id)


def can_view_admin(chat_id, user_id):
    return is_superuser(user_id) or is_approved_user(chat_id, user_id)


def build_help_keyboard(user_id, chat_id=None):
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

    admin_row = []
    if can_view_admin(chat_id, user_id):
        admin_row.append(
            InlineKeyboardButton("🔐 Admin", callback_data="help_admin")
        )

    if admin_row:
        keyboard.append(admin_row)

    keyboard.append(
        [
            InlineKeyboardButton(
                "📢 Channel",
                url="https://t.me/trisfproject",
            )
        ]
    )

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
    keyboard = build_help_keyboard(user_id, chat_id)

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

    if data == "help_done":
        try:
            await query.delete_message()
        except Exception:
            await query.edit_message_text("✅ Done")
        return

    if data == "help_back":
        keyboard = build_help_keyboard(user_id, chat_id)
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
            "/todo done <id>"
        )

        if can_view_admin(chat_id, user_id):
            text += (
                "\n/todo add <text>\n"
                "/todo delete <id>"
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
            "Available to:\n"
            "Approved users\n"
            "Group admins\n"
            "Superusers",
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
            "/chatid",
            reply_markup=submenu_keyboard(),
        )
        return

    if data == "help_admin":
        if is_superuser(user_id):
            text = (
                "🔐 Admin tools\n\n"
                "/approve\n"
                "/revoke\n"
                "/approvelist\n\n"
                "/groups\n"
                "/allowgroup\n"
                "/allowlist\n\n"
                "/export\n"
                "/import"
            )
        else:
            text = (
                "🔐 Admin tools\n\n"
                "Some admin commands require superuser access."
            )

        await query.edit_message_text(
            text,
            reply_markup=submenu_keyboard(),
        )
        return
