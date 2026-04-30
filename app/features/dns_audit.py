import csv
import os
import socket
import tempfile

import httpx
from ipwhois import IPWhois
from telegram import Update
from telegram.ext import ContextTypes

from app.permissions import is_superuser

try:
    from cloudflare import Cloudflare
except ImportError:
    Cloudflare = None

DNS_AUDIT_TYPES = {"A", "AAAA", "CNAME"}
CLOUDFLARE_ORIGIN_ERROR_CODES = {521, 522, 523, 524, 525, 526}


def get_field(value, field):
    if isinstance(value, dict):
        return value[field]

    return getattr(value, field)


def get_optional_field(value, field, default=None):
    if isinstance(value, dict):
        return value.get(field, default)

    return getattr(value, field, default)


def detect_provider(ip):
    try:
        lookup = IPWhois(ip).lookup_rdap()
        org = lookup.get("network", {}).get("name", "")

        if not org:
            return "unknown"

        org = org.lower()

        if "google" in org:
            return "GCP"

        if "amazon" in org:
            return "AWS"

        if "microsoft" in org:
            return "Azure"

        if "huawei" in org:
            return "Huawei"

        if "alibaba" in org:
            return "Alibaba"

        if "aliyun" in org:
            return "Alibaba"

        if "alicloud" in org:
            return "Alibaba"

        if "tencent" in org:
            return "Tencent"

        if "oracle" in org:
            return "OCI"

        if "cloudflare" in org:
            return "Cloudflare"

        if "wowrack" in org:
            return "Wowrack"

        if "biznet" in org:
            return "Biznet"

        if "digitalocean" in org:
            return "DigitalOcean"

        if "linode" in org:
            return "Linode"

        return org
    except Exception:
        return "unknown"


async def dns_audit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_superuser(user_id):
        await update.message.reply_text(
            "⛔ You do not have permission to run this command."
        )
        return

    if Cloudflare is None:
        await update.message.reply_text("❌ Cloudflare SDK not installed.")
        return

    token = os.getenv("CF_API_TOKEN")

    if not token:
        await update.message.reply_text("❌ CF_API_TOKEN not configured.")
        return

    if not context.args:
        await update.message.reply_text(
            "Usage:\n"
            "/dns_audit example.com\n"
            "/dns_audit all"
        )
        return

    zone_arg = context.args[0].lower()

    await update.message.reply_text(f"🌐 DNS audit started: {zone_arg}")

    cf = Cloudflare(api_token=token)

    try:
        if zone_arg == "all":
            zones = list(cf.zones.list())
        else:
            zones = list(cf.zones.list(name=zone_arg))
    except Exception as exc:
        await update.message.reply_text(f"❌ Cloudflare API error: {str(exc)}")
        return

    if not zones:
        await update.message.reply_text("❌ Zone not found")
        return

    for zone in zones:
        zone_name = get_field(zone, "name")
        zone_id = get_field(zone, "id")

        try:
            records = list(cf.dns.records.list(zone_id=zone_id))
        except Exception:
            continue

        active_records = []
        inactive_records = []
        cloudflare_origin_errors = 0

        for record in records:
            record_type = get_field(record, "type")

            if record_type not in DNS_AUDIT_TYPES:
                continue

            record_name = get_field(record, "name")
            record_content = get_field(record, "content")
            record_proxied = bool(get_optional_field(record, "proxied", False))
            ip = ""
            provider = "unknown"

            if record_proxied:
                ip = record_content or "dns_failed"
            else:
                try:
                    ip = socket.gethostbyname(record_name)
                except Exception:
                    ip = "dns_failed"

            url = f"https://{record_name}"
            final_url = ""

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.head(
                        url,
                        timeout=5,
                        follow_redirects=True,
                    )

                    if response.status_code == 405:
                        response = await client.get(
                            url,
                            timeout=5,
                            follow_redirects=True,
                        )

                status_code = response.status_code
                final_url = str(response.url)
            except Exception:
                status_code = None

            if ip == "dns_failed":
                audit_status = "inactive"
                https_status = "dns_failed"
            elif status_code is None:
                audit_status = "inactive"
                https_status = "timeout"
            elif "/login" in final_url:
                audit_status = "active"
                https_status = str(status_code)
            elif status_code in CLOUDFLARE_ORIGIN_ERROR_CODES:
                audit_status = "inactive"
                https_status = str(status_code)
                cloudflare_origin_errors += 1
            elif status_code >= 500:
                audit_status = "inactive"
                https_status = str(status_code)
            else:
                audit_status = "active"
                https_status = str(status_code)

            if ip != "dns_failed":
                provider = detect_provider(ip)

            row = [
                record_name,
                ip,
                record_type,
                audit_status,
                provider,
                https_status,
            ]

            if audit_status == "active":
                active_records.append(row)
            else:
                inactive_records.append(row)

        if not active_records and not inactive_records:
            continue

        header = [
            "record",
            "ip",
            "type",
            "status",
            "provider",
            "https_status",
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

        await update.message.reply_text(
            "DNS audit completed\n\n"
            f"Active records: {len(active_records)}\n"
            f"Inactive records: {len(inactive_records)}\n"
            f"Cloudflare origin errors detected: {cloudflare_origin_errors}"
        )
