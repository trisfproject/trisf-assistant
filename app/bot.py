import os

from dotenv import load_dotenv
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.features.approvals import approve, approvelist, revoke
from app.features.health import health, status
from app.features.notes import delete, lookup, notes, save, update_note
from app.scheduler import reminder_worker

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")


# =========================================================
# MAIN
# =========================================================

def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("save", save))
    app.add_handler(CommandHandler("update", update_note))
    app.add_handler(CommandHandler("delete", delete))
    app.add_handler(CommandHandler("notes", notes))

    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("revoke", revoke))
    app.add_handler(CommandHandler("approvelist", approvelist))

    app.add_handler(CommandHandler("health", health))
    app.add_handler(CommandHandler("status", status))

    app.add_handler(MessageHandler(filters.COMMAND, lookup))

    async def post_init(app):
        app.create_task(reminder_worker(app))

    app.post_init = post_init

    print("trisf-assistant bot running")

    app.run_polling()
