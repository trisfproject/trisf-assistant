import datetime
import json
import re

from app.db import conn
from app.messages import WRITE_DENIED
from app.permissions import is_writer
from app.runtime import check_group


DELAY_RE = re.compile(r"^(\d+)([mhd])$")


def format_delay(value):
    match = DELAY_RE.match(value)
    if not match:
        return value

    amount = int(match.group(1))
    unit = match.group(2)
    labels = {
        "m": ("minute", "minutes"),
        "h": ("hour", "hours"),
        "d": ("day", "days"),
    }
    singular, plural = labels[unit]
    label = singular if amount == 1 else plural

    return f"{amount} {label}"


def parse_delay(value):
    match = DELAY_RE.match(value)
    if not match:
        return None

    amount = int(match.group(1))
    unit = match.group(2)

    if unit == "m":
        return datetime.timedelta(minutes=amount)
    if unit == "h":
        return datetime.timedelta(hours=amount)
    if unit == "d":
        return datetime.timedelta(days=amount)

    return None


async def remind(update, context):
    if not await check_group(update):
        return

    chat = update.effective_chat.id
    user = update.effective_user.id

    if len(context.args) < 2:
        await update.message.reply_text("📘 Usage:\n/remind 10m message")
        return

    delay = parse_delay(context.args[0])
    if delay is None:
        await update.message.reply_text("📘 Usage:\n/remind 10m message")
        return

    if not is_writer(chat, user):
        await update.message.reply_text(WRITE_DENIED)
        return

    requester = update.effective_user
    reminder_text = " ".join(context.args[1:])
    message = json.dumps(
        {
            "text": reminder_text,
            "requester": {
                "id": requester.id,
                "full_name": requester.full_name,
            },
            "thread_id": update.message.message_thread_id,
        }
    )
    remind_at = datetime.datetime.now() + delay

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO reminders (chat_id,user_id,message,remind_at)
        VALUES (%s,%s,%s,%s)
        """,
        (chat, user, message, remind_at),
    )

    await update.message.reply_text(
        f"⏰ Reminder scheduled for {requester.mention_html()} in {format_delay(context.args[0])}",
        parse_mode="HTML",
    )
