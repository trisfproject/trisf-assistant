import re
import logging
from datetime import datetime, timedelta

from pymysql.cursors import DictCursor
from telegram import Update
from telegram.ext import ContextTypes

from app.db import get_connection


logger = logging.getLogger(__name__)


def format_duration(seconds):
    minutes = seconds // 60

    if minutes < 1:
        return f"{seconds}s"

    if minutes < 60:
        return f"{minutes} minutes"

    hours = minutes // 60
    return f"{hours} hours"


def calculate_duration_minutes(started_at, ended_at):
    if ended_at is None:
        return 0

    delta = ended_at - started_at
    return int(delta.total_seconds() // 60)


async def down_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "⚠️ Usage:\n/down <service> [note]"
        )
        return

    service = context.args[0]
    note = " ".join(context.args[1:]) if len(context.args) > 1 else None
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id
        FROM downtime_events
        WHERE chat_id=%s
        AND service=%s
        AND status='open'
        """,
        (chat_id, service),
    )

    existing = cur.fetchone()

    if existing:
        await update.message.reply_text(
            f"⚠️ {service} already marked as DOWN."
        )
        return

    cur.execute(
        """
        INSERT INTO downtime_events
        (chat_id, service, note, reported_by, started_at)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (chat_id, service, note, user_id, datetime.utcnow()),
    )

    conn.commit()

    await update.message.reply_text(
        f"📉 Downtime started\n\n"
        f"Service: {service}\n"
        f"Reported by: {update.effective_user.first_name}"
    )


async def up_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "⚠️ Usage:\n/up <service>"
        )
        return

    service = context.args[0]
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    conn = get_connection()
    cur = conn.cursor(DictCursor)

    cur.execute(
        """
        SELECT *
        FROM downtime_events
        WHERE chat_id=%s
        AND service=%s
        AND status='open'
        ORDER BY started_at DESC
        LIMIT 1
        """,
        (chat_id, service),
    )

    row = cur.fetchone()

    if not row:
        await update.message.reply_text(
            f"⚠️ {service} is not marked as DOWN."
        )
        return

    started = row["started_at"]
    now = datetime.utcnow()
    duration = int((now - started).total_seconds())

    cur.execute(
        """
        UPDATE downtime_events
        SET status='closed',
        resolved_by=%s,
        ended_at=%s
        WHERE id=%s
        """,
        (user_id, now, row["id"]),
    )

    conn.commit()

    await update.message.reply_text(
        f"✅ Downtime resolved\n\n"
        f"Service: {service}\n"
        f"Duration: {format_duration(duration)}"
    )


async def downlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    conn = get_connection()
    cur = conn.cursor(DictCursor)

    cur.execute(
        """
        SELECT service, started_at
        FROM downtime_events
        WHERE chat_id=%s
        AND status='open'
        ORDER BY started_at ASC
        """,
        (chat_id,),
    )

    rows = cur.fetchall()

    if not rows:
        await update.message.reply_text(
            "✅ No active downtime."
        )
        return

    text = "📉 Active downtime\n\n"

    for row in rows:
        seconds = int(
            (datetime.utcnow() - row["started_at"]).total_seconds()
        )
        text += f"{row['service']} ({format_duration(seconds)})\n"

    await update.message.reply_text(text)


async def downhistory_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    now = datetime.utcnow()
    arg = context.args[0] if context.args else None

    conn = get_connection()
    cur = conn.cursor(DictCursor)

    if not arg:
        year = now.year
        month = now.month
        month_str = f"{month:02d}"
        history_title = f"{year}-{month_str}"
        start_date = datetime(now.year, now.month, 1)
        end_date = now
    else:
        match = re.match(r"^(\d{4})-(\d{1,2})$", arg)

        if match:
            year = int(match.group(1))
            month = int(match.group(2))

            if month < 1 or month > 12:
                await update.message.reply_text(
                    "⚠️ Invalid format. Use:\n\n"
                    "/downhistory 2025-04"
                )
                return

            month_str = f"{month:02d}"
            history_title = f"{year}-{month_str}"
            start_date = datetime(year, month, 1)

            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)

            logger.info(
                "downhistory filter month: %s-%s",
                year,
                month,
            )
        elif arg == "last":
            start_date = datetime(now.year, now.month, 1) - timedelta(days=1)
            start_date = datetime(start_date.year, start_date.month, 1)
            end_date = datetime(now.year, now.month, 1)
            month_str = f"{start_date.month:02d}"
            history_title = f"{start_date.year}-{month_str}"
        elif arg == "7d":
            start_date = now - timedelta(days=7)
            end_date = now
            history_title = "last 7 days"
        elif arg == "all":
            start_date = datetime(2000, 1, 1)
            end_date = now
            history_title = "all"
        else:
            await update.message.reply_text(
                "⚠️ Invalid format. Use:\n\n"
                "/downhistory 2025-04"
            )
            return

    cur.execute(
        """
        SELECT service, started_at, ended_at
        FROM downtime_events
        WHERE chat_id=%s
        AND started_at >= %s
        AND started_at < %s
        ORDER BY started_at DESC
        """,
        (chat_id, start_date, end_date),
    )

    rows = cur.fetchall()

    if not rows:
        await update.message.reply_text(
            f"📊 Downtime history {history_title}\n\n"
            "No downtime incidents recorded."
        )
        return

    lines = []
    total_incidents = len(rows)
    total_minutes = 0

    for idx, row in enumerate(rows, start=1):
        service = row["service"]
        started_at = row["started_at"]
        ended_at = row["ended_at"]

        minutes = calculate_duration_minutes(started_at, ended_at)
        total_minutes += minutes

        lines.append(f"{idx}. {service} ({minutes} minutes)")

    message = (
        f"📊 Downtime history {history_title}\n\n"
        f"Total incidents: {total_incidents}\n"
        f"Total downtime: {total_minutes} minutes\n\n"
        + "\n".join(lines)
    )

    await update.message.reply_text(message)
