import os
import logging
import sys
import contextlib
import asyncio

from dotenv import load_dotenv
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.features.approvals import approve, approvelist, revoke
from app.features.admin_tools import (
    admins_command,
    demote_command,
    promote_command,
)
from app.features.afk import (
    afk_auto_clear,
    afk_check_mentions,
    afk_command,
)
from app.features.audit import audit
from app.features.backup import (
    export_handler,
    import_document_handler,
    import_handler,
)
from app.features.chatid import chatid
from app.features.coffee import coffee_command
from app.features.delete_message import delete_command
from app.features.dns_audit import dns_audit_command
from app.features.downtime import (
    down_command,
    downhistory_command,
    downlist_command,
    up_command,
)
from app.features.ghost import ghost_command
from app.features.groups import allowedgroups, allowgroup, removegroup
from app.features.health import health, status
from app.features.help import help_button_handler, help_command
from app.features.id import show_id
from app.features.network import (
    dns_command,
    http_command,
    ping_command,
    whois_command,
)
from app.features.notes import delete, lookup, notes, save, update_note
from app.features.oncall import oncall_handler
from app.features.password import password_command
from app.features.pin import (
    cleanup_pin_service_message,
    pin_command,
    unpin_command,
)
from app.features.purge import purge_command
from app.features.reminders import remind
from app.features.todos import todo
from app.features.user_moderation import (
    ban_command,
    kick_command,
    unban_command,
)
from app.scheduler import reminder_worker

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
LOG_FILE = "/app/logs/bot.log"
logger = logging.getLogger(__name__)


def configure_logging():
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )


# =========================================================
# MAIN
# =========================================================

def main():
    configure_logging()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("save", save))
    app.add_handler(CommandHandler("update", update_note))
    app.add_handler(CommandHandler("delete", delete))
    app.add_handler(CommandHandler("notes", notes))

    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("revoke", revoke))
    app.add_handler(CommandHandler("approvelist", approvelist))
    app.add_handler(CommandHandler("promote", promote_command))
    app.add_handler(CommandHandler("demote", demote_command))
    app.add_handler(CommandHandler("admins", admins_command))
    app.add_handler(CommandHandler("del", delete_command))
    app.add_handler(CommandHandler("purge", purge_command))
    app.add_handler(CommandHandler("kick", kick_command))
    app.add_handler(CommandHandler("ban", ban_command))
    app.add_handler(CommandHandler("unban", unban_command))

    app.add_handler(CommandHandler("allowgroup", allowgroup))
    app.add_handler(CommandHandler("removegroup", removegroup))
    app.add_handler(CommandHandler("allowedgroups", allowedgroups))
    app.add_handler(CommandHandler("allowlist", allowedgroups))
    app.add_handler(CommandHandler("groups", allowedgroups))

    app.add_handler(CommandHandler("todo", todo))
    app.add_handler(CommandHandler("remind", remind))
    app.add_handler(CommandHandler("audit", audit))
    app.add_handler(CommandHandler("down", down_command))
    app.add_handler(CommandHandler("up", up_command))
    app.add_handler(CommandHandler("downlist", downlist_command))
    app.add_handler(CommandHandler("downhistory", downhistory_command))
    app.add_handler(CommandHandler("afk", afk_command))
    app.add_handler(CommandHandler("oncall", oncall_handler), group=-1)
    app.add_handler(CommandHandler("export", export_handler))
    app.add_handler(CommandHandler("import", import_handler))

    app.add_handler(CommandHandler("health", health))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("id", show_id))
    app.add_handler(CommandHandler("chatid", chatid))
    app.add_handler(CommandHandler("ping", ping_command))
    app.add_handler(CommandHandler("dns", dns_command))
    app.add_handler(CommandHandler("dns-audit", dns_audit_command))
    app.add_handler(CommandHandler("http", http_command))
    app.add_handler(CommandHandler("whois", whois_command))
    app.add_handler(CommandHandler("pw", password_command))
    app.add_handler(CommandHandler("coffee", coffee_command))
    app.add_handler(CommandHandler("ghost", ghost_command))
    app.add_handler(CommandHandler("pin", pin_command))
    app.add_handler(CommandHandler("unpin", unpin_command))
    app.add_handler(
        MessageHandler(filters.StatusUpdate.PINNED_MESSAGE, cleanup_pin_service_message),
        group=-1,
    )
    app.add_handler(CallbackQueryHandler(help_button_handler, pattern="^help_"))

    app.add_handler(
        MessageHandler(
            filters.Document.FileExtension("json"),
            import_document_handler,
        )
    )
    app.add_handler(MessageHandler(filters.TEXT, lookup))
    app.add_handler(MessageHandler(filters.ALL, afk_check_mentions), group=1)
    app.add_handler(MessageHandler(filters.ALL, afk_auto_clear), group=2)

    async def post_init(app):
        app.bot_data["reminder_worker_task"] = asyncio.create_task(
            reminder_worker(app)
        )

    async def stop_background_tasks(app):
        task = app.bot_data.pop("reminder_worker_task", None)
        if not task:
            return

        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

    app.post_init = post_init
    app.post_stop = stop_background_tasks
    app.post_shutdown = stop_background_tasks

    logger.info("trisf-assistant bot running")

    app.run_polling()
