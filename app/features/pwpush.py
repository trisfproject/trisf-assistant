from telegram import Update
from telegram.ext import ContextTypes
import requests
import secrets


PWPUSH_API = "https://phoenix.cygnuss-district8.com/p.json"
PWPUSH_BASE = "https://phoenix.cygnuss-district8.com/p/"

PASSPHRASE_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789"


def generate_passphrase(length=8):
    return "".join(
        secrets.choice(PASSPHRASE_CHARS)
        for _ in range(length)
    )


def create_secret(payload, passphrase=None):
    data = {
        "payload": payload,
        "expire_after_days": 7,
        "expire_after_views": 5,
        "deletable_by_viewer": "true",
        "retrieval_step": "true",
    }

    if passphrase:
        data["passphrase"] = passphrase

    response = requests.post(PWPUSH_API, data=data)

    if response.status_code != 200:
        print("pwpush error:", response.status_code)
        print(response.text)

        return None

    return response.json().get("url_token")


def _command_body(message_text):
    if not message_text:
        return ""

    parts = message_text.split(maxsplit=1)
    if len(parts) < 2:
        return ""

    return parts[1].strip()


def _reply_secret(message):
    if not message.reply_to_message:
        return None

    return message.reply_to_message.text or message.reply_to_message.caption


def _looks_like_passphrase(value):
    return value.isdigit()


async def push_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    body = _command_body(message.text or message.caption)
    reply_secret = _reply_secret(message)
    secret = None
    passphrase = None
    lock_mode = False

    if body:
        if body == "lock" or body.startswith("lock "):
            lock_mode = True
            lock_body = body[4:].strip()

            if reply_secret:
                passphrase = lock_body or None
            elif lock_body:
                lock_parts = lock_body.split(maxsplit=1)

                if len(lock_parts) > 1 and _looks_like_passphrase(lock_parts[0]):
                    passphrase = lock_parts[0]
                    secret = lock_parts[1]
                else:
                    secret = lock_body
        else:
            secret = body

    if not secret and reply_secret:
        secret = reply_secret

    if not secret:
        await message.reply_text(
            "⚠️ Usage:\n"
            "/push <secret>\n"
            "reply message + /push\n"
            "/push lock <secret>\n"
            "reply message + /push lock"
        )
        return

    if lock_mode and not passphrase:
        passphrase = generate_passphrase()

    token = create_secret(secret, passphrase)

    if not token:
        await message.reply_text(
            "❌ Failed to create secret link"
        )
        return

    link = f"{PWPUSH_BASE}{token}"

    if passphrase:
        response_message = (
            "🔐 Secure secret created\n\n"
            f"Secret link:\n{link}\n\n"
            f"Passphrase:\n{passphrase}\n\n"
            "Views: 5\n"
            "Expires: 7 days"
        )
    else:
        response_message = (
            "🔐 Secret link created\n\n"
            f"{link}\n\n"
            "Views: 5\n"
            "Expires: 7 days"
        )

    await message.reply_text(response_message)

    try:
        if message.reply_to_message:
            await context.bot.delete_message(
                update.effective_chat.id,
                message.reply_to_message.message_id,
            )

        await context.bot.delete_message(
            update.effective_chat.id,
            message.message_id,
        )
    except Exception:
        pass
