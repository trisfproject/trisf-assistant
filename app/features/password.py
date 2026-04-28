from telegram import Update
from telegram.ext import ContextTypes
import secrets


UPPER = "ABCDEFGHJKLMNPQRSTUVWXYZ"
LOWER = "abcdefghijkmnpqrstuvwxyz"
DIGITS = "23456789"
SYMBOLS = "!@$%&*+=?"

CHARSET = UPPER + LOWER + DIGITS + SYMBOLS


def generate_password(length):
    return "".join(
        secrets.choice(CHARSET)
        for _ in range(length)
    )


async def password_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    length = 16

    if context.args:
        try:
            length = int(context.args[0])
        except Exception:
            await update.message.reply_text(
                "⚠️ Usage: /pw [length]"
            )
            return

    if length < 8 or length > 64:
        await update.message.reply_text(
            "⚠️ Length must be between 8 and 64."
        )
        return

    password = generate_password(length)

    await update.message.reply_text(
        f"🔐 Generated password ({length} chars):\n`{password}`",
        parse_mode="Markdown",
    )
