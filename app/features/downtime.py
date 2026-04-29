import re
from datetime import datetime, timedelta

from pymysql.cursors import DictCursor
from telegram import Update
from telegram.ext import ContextTypes

from app.db import get_connection


def format_duration(seconds):
    minutes = seconds // 60

    if minutes < 1:
        return f"{seconds}s"

    if minutes < 60:
        return f"{minutes} minutes"

    hours = minutes // 60
    return f"{hours} hours"


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
    mode = context.args[0] if context.args else "month"

    conn = get_connection()
    cur = conn.cursor(DictCursor)

    if re.fullmatch(r"\d{4}-\d{1,2}", mode):
        year, month = mode.split("-")
        year = int(year)
        month = int(month)

        if month < 1 or month > 12:
            await update.message.reply_text(
                "⚠️ Invalid format. Use:\n"
                "YYYY-MM\n"
                "example:\n"
                "/downhistory 2025-04"
            )
            return

        start = datetime(year, month, 1)

        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)
    elif mode == "last":
        start = datetime(now.year, now.month, 1) - timedelta(days=1)
        start = datetime(start.year, start.month, 1)
        end = datetime(now.year, now.month, 1)
    elif mode == "7d":
        start = now - timedelta(days=7)
        end = now
    elif mode == "all":
        start = datetime(2000, 1, 1)
        end = now
    elif mode == "month":
        start = datetime(now.year, now.month, 1)
        end = now
    else:
        await update.message.reply_text(
            "⚠️ Invalid format. Use:\n"
            "YYYY-MM\n"
            "example:\n"
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
        (chat_id, start, end),
    )

    rows = cur.fetchall()

    if not rows:
        await update.message.reply_text(
            "📊 No downtime history."
        )
        return

    text = "📊 Downtime history\n\n"

    for row in rows:
        ended_at = row["ended_at"] or datetime.utcnow()
        seconds = int(
            (ended_at - row["started_at"]).total_seconds()
        )
        text += f"{row['service']} ({format_duration(seconds)})\n"

    await update.message.reply_text(text)
