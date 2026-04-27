import datetime
import os

from dotenv import load_dotenv

from app.db import conn
from app.messages import GROUP_NOT_ALLOWED
from app.permissions import is_superuser


load_dotenv()

BOT_MODE = os.getenv("BOT_MODE", "restricted")
OWNER_CONTACT = os.getenv("OWNER_CONTACT", "@trisf")
START_TIME = datetime.datetime.now()


def log_action(chat, user, action, target="", meta=""):
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO audit_log
        (chat_id,user_id,action,target,metadata)
        VALUES (%s,%s,%s,%s,%s)
        """,
        (chat, user, action, target, meta),
    )


def format_uptime():
    delta = datetime.datetime.now() - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours}h {minutes}m"


def is_group_allowed(chat):
    if BOT_MODE == "open":
        return True

    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM allowed_groups WHERE chat_id=%s",
        (chat,),
    )

    return cursor.fetchone() is not None


async def check_group(update):
    if is_superuser(update.effective_user.id):
        return True

    if not is_group_allowed(update.effective_chat.id):
        await update.message.reply_text(
            GROUP_NOT_ALLOWED(OWNER_CONTACT)
        )
        return False

    return True


async def is_admin(update, context):
    if is_superuser(update.effective_user.id):
        return True

    if not is_group_allowed(update.effective_chat.id):
        await update.message.reply_text(
            GROUP_NOT_ALLOWED(OWNER_CONTACT)
        )
        return False

    admins = await context.bot.get_chat_administrators(
        update.effective_chat.id
    )

    return any(
        admin.user.id == update.effective_user.id
        for admin in admins
    )
