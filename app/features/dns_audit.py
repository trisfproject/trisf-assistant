import csv
import os
import socket
import tempfile

import CloudFlare
import httpx
from ipwhois import IPWhois
from telegram import Update
from telegram.ext import ContextTypes

from app.permissions import is_superuser

DNS_AUDIT_TYPES = {"A", "AAAA", "CNAME"}


async def dns_audit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_superuser(user_id):
        await update.message.reply_text(
            "⛔ You do not have permission to run this command."
        )
        return

    cf_api_token = os.getenv("CF_API_TOKEN")

    if not cf_api_token:
        await update.message.reply_text("❌ CF_API_TOKEN not configured")
        return

    if not context.args:
        await update.message.reply_text(
            "Usage:\n"
            "/dns-audit example.com\n"
            "/dns-audit all"
        )
        return

    zone_arg = context.args[0].lower()

    await update.message.reply_text(f"🌐 DNS audit started: {zone_arg}")

    cf = CloudFlare.CloudFlare(token=cf_api_token)

    try:
        if zone_arg == "all":
            zones = cf.zones.get()
        else:
            zones = cf.zones.get(params={"name": zone_arg})
    except Exception as exc:
        await update.message.reply_text(f"❌ Cloudflare API error: {str(exc)}")
        return

    if not zones:
        await update.message.reply_text("❌ Zone not found")
        return

    for zone in zones:
        zone_name = zone["name"]
        zone_id = zone["id"]

        try:
            records = cf.zones.dns_records.get(zone_id)
        except Exception:
            continue

        active_records = []
        inactive_records = []

        for record in records:
            if record["type"] not in DNS_AUDIT_TYPES:
                continue

            record_name = record["name"]
            record_type = record["type"]
            ip = ""
            provider = "unknown"
            http_status = "n/a"
            status = "inactive"

            try:
                ip = socket.gethostbyname(record_name)
                status = "active"
            except Exception:
                ip = "dns_failed"
                status = "inactive"

            if status == "active":
                try:
                    response = httpx.get(
                        f"http://{record_name}",
                        timeout=3,
                    )
                    http_status = str(response.status_code)
                except Exception:
                    http_status = "timeout"

                try:
                    obj = IPWhois(ip)
                    result = obj.lookup_rdap()
                    provider = result["network"]["name"]
                except Exception:
                    provider = "unknown"

            row = [
                record_name,
                ip,
                record_type,
                provider,
                status,
                http_status,
            ]

            if status == "active":
                active_records.append(row)
            else:
                inactive_records.append(row)

        if not active_records and not inactive_records:
            continue

        header = [
            "record",
            "ip",
            "type",
            "provider",
            "status",
            "http_status",
        ]

        active_file = tempfile.NamedTemporaryFile(delete=False, suffix="_active.csv")
        inactive_file = tempfile.NamedTemporaryFile(delete=False, suffix="_inactive.csv")
        active_file.close()
        inactive_file.close()

        with open(active_file.name, "w", newline="") as file_handle:
            writer = csv.writer(file_handle)
            writer.writerow(header)
            writer.writerows(active_records)

        with open(inactive_file.name, "w", newline="") as file_handle:
            writer = csv.writer(file_handle)
            writer.writerow(header)
            writer.writerows(inactive_records)

        with open(active_file.name, "rb") as document:
            await update.message.reply_document(
                document=document,
                filename=f"{zone_name}_active.csv",
            )

        with open(inactive_file.name, "rb") as document:
            await update.message.reply_document(
                document=document,
                filename=f"{zone_name}_inactive.csv",
            )

        os.unlink(active_file.name)
        os.unlink(inactive_file.name)
