import datetime
import json
import os
import tempfile

from app.db import conn
from app.messages import ACCESS_DENIED
from app.permissions import is_superuser
from app.runtime import check_group


IMPORT_WAITING = set()
EXPORT_TABLE_KEYS = (
    "notes",
    "todos",
    "reminders",
    "approvals",
    "oncall_status",
)

BACKUP_TABLES = {
    "notes": {
        "table": "saved_notes",
        "columns": [
            "chat_id",
            "key_name",
            "content",
            "created_by",
            "created_at",
            "updated_at",
        ],
    },
    "todos": {
        "table": "todos",
        "columns": [
            "id",
            "chat_id",
            "task",
            "created_by",
            "completed",
            "created_at",
        ],
    },
    "reminders": {
        "table": "reminders",
        "columns": [
            "id",
            "chat_id",
            "user_id",
            "message",
            "remind_at",
            "sent",
        ],
    },
    "approvals": {
        "table": "approved_users",
        "columns": [
            "chat_id",
            "user_id",
            "username",
            "full_name",
            "approved_at",
        ],
    },
    "allowed_groups": {
        "table": "allowed_groups",
        "columns": [
            "chat_id",
            "added_at",
        ],
    },
    "oncall_status": {
        "table": "oncall_status",
        "columns": [
            "chat_id",
            "user_id",
            "username",
            "updated_at",
        ],
    },
}

PROGRESS_LABELS = [
    ("notes", "notes"),
    ("todos", "todos"),
    ("reminders", "reminders"),
    ("approvals", "approvals"),
    ("allowed_groups", "allowed_groups"),
    ("oncall_status", "oncall"),
]


def serialize_value(value):
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat(sep=" ")
    if isinstance(value, bytes):
        return value.decode()
    return value


def normalize_value(value):
    if value == "":
        return None
    return value


def select_rows(key, chat, all_groups=False):
    config = BACKUP_TABLES[key]
    table = config["table"]
    columns = config["columns"]
    cursor = conn.cursor()

    if all_groups:
        cursor.execute(
            f"SELECT {','.join(columns)} FROM {table} ORDER BY chat_id"
        )
    else:
        cursor.execute(
            f"SELECT {','.join(columns)} FROM {table} WHERE chat_id=%s",
            (chat,),
        )

    rows = []
    for row in cursor.fetchall():
        rows.append({
            column: serialize_value(value)
            for column, value in zip(columns, row)
        })

    return rows


def build_backup(chat, all_groups=False):
    data = {
        "format": "trisf-assistant-backup",
        "version": 1,
        "scope": "all" if all_groups else "chat",
        "chat_id": None if all_groups else chat,
        "exported_at": datetime.datetime.now().isoformat(sep=" "),
        "tables": {},
    }

    for key in EXPORT_TABLE_KEYS:
        data["tables"][key] = select_rows(key, chat, all_groups=all_groups)

    return data


def validate_backup(data):
    if not isinstance(data, dict):
        return False
    if data.get("format") != "trisf-assistant-backup":
        return False
    tables = data.get("tables")
    if not isinstance(tables, dict):
        return False

    for key in EXPORT_TABLE_KEYS:
        if key not in tables or not isinstance(tables[key], list):
            return False

    if "allowed_groups" in tables and not isinstance(tables["allowed_groups"], list):
        return False

    return True


def delete_existing_rows(key, chat):
    table = BACKUP_TABLES[key]["table"]
    cursor = conn.cursor()

    cursor.execute(
        f"DELETE FROM {table} WHERE chat_id=%s",
        (chat,),
    )


def insert_rows(key, rows, chat):
    config = BACKUP_TABLES[key]
    table = config["table"]
    columns = [
        column for column in config["columns"]
        if not (key in ("todos", "reminders") and column == "id")
    ]
    placeholders = ",".join(["%s"] * len(columns))
    cursor = conn.cursor()

    for row in rows:
        values = []
        for column in columns:
            value = normalize_value(row.get(column))
            if column == "chat_id":
                value = chat
            values.append(value)

        cursor.execute(
            f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})",
            values,
        )


async def export_handler(update, context):
    if not is_superuser(update.effective_user.id):
        await update.message.reply_text(ACCESS_DENIED)
        return

    if not await check_group(update):
        return

    all_groups = bool(context.args and context.args[0].lower() == "all")

    await update.message.reply_text("📦 Export dimulai…")

    chat = update.effective_chat.id
    data = build_backup(chat, all_groups=all_groups)
    filename = f"trisf-assistant-backup-{datetime.date.today().isoformat()}.json"
    path = os.path.join(tempfile.gettempdir(), filename)

    with open(path, "w", encoding="utf-8") as backup_file:
        json.dump(data, backup_file, ensure_ascii=False, indent=2)

    with open(path, "rb") as backup_file:
        await update.message.reply_document(
            document=backup_file,
            filename=filename,
        )

    os.remove(path)
    await update.message.reply_text("✅ Export selesai")


async def import_handler(update, context):
    if not is_superuser(update.effective_user.id):
        await update.message.reply_text(ACCESS_DENIED)
        return

    if not await check_group(update):
        return

    IMPORT_WAITING.add((update.effective_chat.id, update.effective_user.id))
    await update.message.reply_text("📥 Kirim file backup JSON untuk restore")


async def import_document_handler(update, context):
    if not update.message or not update.message.document:
        return

    chat = update.effective_chat.id
    user = update.effective_user.id
    wait_key = (chat, user)

    if wait_key not in IMPORT_WAITING:
        return

    if not is_superuser(user):
        IMPORT_WAITING.discard(wait_key)
        await update.message.reply_text(ACCESS_DENIED)
        return

    if not await check_group(update):
        IMPORT_WAITING.discard(wait_key)
        return

    document = update.message.document
    if not document.file_name or not document.file_name.endswith(".json"):
        IMPORT_WAITING.discard(wait_key)
        await update.message.reply_text("❌ Format backup tidak valid")
        return

    try:
        telegram_file = await document.get_file()
        payload = await telegram_file.download_as_bytearray()
        data = json.loads(payload.decode("utf-8"))
    except Exception:
        IMPORT_WAITING.discard(wait_key)
        await update.message.reply_text("❌ Format backup tidak valid")
        return

    if not validate_backup(data):
        IMPORT_WAITING.discard(wait_key)
        await update.message.reply_text("❌ Format backup tidak valid")
        return

    tables = data["tables"]

    try:
        cursor = conn.cursor()
        cursor.execute("START TRANSACTION")

        for key, _label in PROGRESS_LABELS:
            if key not in tables:
                continue
            delete_existing_rows(key, chat)
            insert_rows(key, tables[key], chat)

        cursor.execute("COMMIT")
    except Exception:
        conn.cursor().execute("ROLLBACK")
        IMPORT_WAITING.discard(wait_key)
        await update.message.reply_text("❌ Format backup tidak valid")
        return

    IMPORT_WAITING.discard(wait_key)

    progress = "\n".join(
        f"{label} ✔"
        for key, label in PROGRESS_LABELS
        if key in tables
    )
    await update.message.reply_text(progress)
    await update.message.reply_text("✅ Import selesai")
