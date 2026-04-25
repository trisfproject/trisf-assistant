import os
import json
import datetime

from dotenv import load_dotenv
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from app.db import conn
from app.permissions import is_superuser, is_writer
from app.scheduler import reminder_worker
from app.messages import *

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_MODE = os.getenv("BOT_MODE", "restricted")
OWNER_CONTACT = os.getenv("OWNER_CONTACT", "@trisf")


# ===============================
# HELPER
# ===============================

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


def is_group_allowed(chat):

    if BOT_MODE == "open":
        return True

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT 1 FROM allowed_groups
        WHERE chat_id=%s
        """,
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

    admins = await context.bot.get_chat_administrators(
        update.effective_chat.id
    )

    return any(
        admin.user.id == update.effective_user.id
        for admin in admins
    )


# ===============================
# SAVE NOTE
# ===============================

async def save(update, context):

    if not await check_group(update):
        return

    chat = update.effective_chat.id
    user = update.effective_user.id

    if not is_writer(chat, user):

        await update.message.reply_text(WRITE_DENIED)
        return

    if len(context.args) < 2:
        return

    key = context.args[0]
    content = " ".join(context.args[1:])

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT IGNORE INTO saved_notes
        (chat_id,key_name,content,created_by)
        VALUES (%s,%s,%s,%s)
        """,
        (chat, key, content, user),
    )

    if cursor.rowcount == 0:

        await update.message.reply_text(
            "⚠️ key sudah ada gunakan /update"
        )
        return

    log_action(chat, user, "save", key)

    await update.message.reply_text("✅ saved")


# ===============================
# UPDATE NOTE
# ===============================

async def update_note(update, context):

    if not await is_admin(update, context):
        await update.message.reply_text(ACCESS_DENIED)
        return

    chat = update.effective_chat.id

    key = context.args[0]
    content = " ".join(context.args[1:])

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE saved_notes
        SET content=%s,updated_at=NOW()
        WHERE chat_id=%s AND key_name=%s
        """,
        (content, chat, key),
    )

    log_action(chat, update.effective_user.id, "update", key)

    await update.message.reply_text("✅ updated")


# ===============================
# DELETE NOTE
# ===============================

async def delete(update, context):

    if not await is_admin(update, context):
        await update.message.reply_text(ACCESS_DENIED)
        return

    chat = update.effective_chat.id
    key = context.args[0]

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM saved_notes
        WHERE chat_id=%s AND key_name=%s
        """,
        (chat, key),
    )

    log_action(chat, update.effective_user.id, "delete", key)

    await update.message.reply_text("🗑 deleted")


# ===============================
# NOTES LIST
# ===============================

async def notes(update, context):

    if not await check_group(update):
        return

    chat = update.effective_chat.id

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT key_name
        FROM saved_notes
        WHERE chat_id=%s
        ORDER BY key_name
        """,
        (chat,),
    )

    rows = cursor.fetchall()

    if not rows:

        await update.message.reply_text("belum ada notes")
        return

    msg = "Available notes:\n\n"

    for r in rows:
        msg += r[0] + "\n"

    await update.message.reply_text(msg)


# ===============================
# KEY LOOKUP
# ===============================

async def lookup(update, context):

    if not await check_group(update):
        return

    chat = update.effective_chat.id

    key = update.message.text.split()[0][1:]

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT content
        FROM saved_notes
        WHERE chat_id=%s AND key_name=%s
        """,
        (chat, key),
    )

    row = cursor.fetchone()

    if row:
        await update.message.reply_text(row[0])


# ===============================
# APPROVE USER
# ===============================

async def approve(update, context):

    if not await is_admin(update, context):
        await update.message.reply_text(ACCESS_DENIED)
        return

    chat = update.effective_chat.id

    if update.message.reply_to_message:

        user = update.message.reply_to_message.from_user

        uid = user.id
        username = user.username
        fullname = user.full_name

    else:

        uid = int(context.args[0])
        username = None
        fullname = None

    cursor = conn.cursor()

    cursor.execute(
        """
        REPLACE INTO approved_users
        (chat_id,user_id,username,full_name)
        VALUES (%s,%s,%s,%s)
        """,
        (chat, uid, username, fullname),
    )

    log_action(chat, update.effective_user.id, "approve", uid)

    await update.message.reply_text("✅ user berhasil di-approve")


# ===============================
# REVOKE USER
# ===============================

async def revoke(update, context):

    if not await is_admin(update, context):
        await update.message.reply_text(ACCESS_DENIED)
        return

    chat = update.effective_chat.id
    uid = int(context.args[0])

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM approved_users
        WHERE chat_id=%s AND user_id=%s
        """,
        (chat, uid),
    )

    log_action(chat, update.effective_user.id, "revoke", uid)

    await update.message.reply_text("🚫 user access dicabut")


# ===============================
# APPROVELIST
# ===============================

async def approvelist(update, context):

    if not await is_admin(update, context):
        await update.message.reply_text(ACCESS_DENIED)
        return

    chat = update.effective_chat.id

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT username,full_name,user_id
        FROM approved_users
        WHERE chat_id=%s
        """,
        (chat,),
    )

    rows = cursor.fetchall()

    if not rows:

        await update.message.reply_text(
            "Belum ada user yang di-approve."
        )
        return

    msg = "Approved users:\n\n"

    for username, fullname, uid in rows:

        if username:
            msg += f"@{username}\n"
        elif fullname:
            msg += f"{fullname}\n"
        else:
            msg += f"{uid}\n"

    await update.message.reply_text(msg)


# ===============================
# REMINDER
# ===============================

async def remind(update, context):

    if not await check_group(update):
        return

    delay = context.args[0]
    message = " ".join(context.args[1:])

    unit = delay[-1]
    value = int(delay[:-1])

    seconds = (
        value * 60
        if unit == "m"
        else value * 3600
        if unit == "h"
        else value * 86400
    )

    remind_at = datetime.datetime.now() + datetime.timedelta(
        seconds=seconds
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO reminders
        (chat_id,user_id,message,remind_at)
        VALUES (%s,%s,%s,%s)
        """,
        (
            update.effective_chat.id,
            update.effective_user.id,
            message,
            remind_at,
        ),
    )

    await update.message.reply_text("⏰ reminder scheduled")


# ===============================
# MAIN
# ===============================

def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("save", save))
    app.add_handler(CommandHandler("update", update_note))
    app.add_handler(CommandHandler("delete", delete))
    app.add_handler(CommandHandler("notes", notes))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("revoke", revoke))
    app.add_handler(CommandHandler("approvelist", approvelist))
    app.add_handler(CommandHandler("remind", remind))

    app.add_handler(
        MessageHandler(filters.COMMAND, lookup)
    )

    async def post_init(app):
        app.create_task(reminder_worker(app))

    app.post_init = post_init

    print("trisf-assistant bot running")

    app.run_polling()