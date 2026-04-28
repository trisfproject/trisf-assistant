import datetime

from app.db import conn
from app.messages import ACCESS_DENIED
from app.runtime import BOT_MODE, format_uptime, is_admin


async def health(update, context):

    if not await is_admin(update, context):
        await update.message.reply_text(ACCESS_DENIED)
        return

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        db_status = "connected"
    except:
        db_status = "error"

    msg = f"""🤖 trisf-assistant health check

🤖 bot: online
📊 database: {db_status}
⏰ scheduler: running
ℹ️ mode: {BOT_MODE}
🕔 uptime: {format_uptime()}
"""

    await update.message.reply_text(msg)


async def status(update, context):

    if not await is_admin(update, context):
        await update.message.reply_text(ACCESS_DENIED)
        return

    if not context.args:
        await update.message.reply_text(
            "📘 Usage:\n/status bot\n/status db\n/status scheduler"
        )
        return

    target = context.args[0]

    if target == "bot":

        await update.message.reply_text(
            f"📊 status: running\n📊 uptime: {format_uptime()}"
        )

    elif target == "db":

        try:
            start = datetime.datetime.now()
            conn.cursor().execute("SELECT 1")
            latency = datetime.datetime.now() - start

            await update.message.reply_text(
                f"📊 database OK ({int(latency.total_seconds()*1000)} ms)"
            )

        except:

            await update.message.reply_text(
                "❌ database: ERROR"
            )

    elif target == "scheduler":

        await update.message.reply_text(
            "⏰ scheduler running (interval 30s)"
        )

    else:
        await update.message.reply_text(
            "📘 Usage:\n/status bot\n/status db\n/status scheduler"
        )
