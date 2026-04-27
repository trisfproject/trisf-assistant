import asyncio
import html
import re
import subprocess
import time
from urllib.parse import urlparse

import aiohttp

from app.runtime import check_group


DNS_TYPES = {"A", "AAAA", "MX", "TXT", "NS", "CNAME"}
MAX_LINES = 20
MAX_CHARS = 3000


def safe_target(value):
    return bool(value and not value.startswith("-"))


def trim_output(lines):
    text = "\n".join(lines[:MAX_LINES]).strip()
    if len(text) > MAX_CHARS:
        return text[:MAX_CHARS] + "\n..."

    return text


def escape(value):
    return html.escape(str(value))


def first_line(value, fallback):
    text = (value or fallback).strip()
    if not text:
        return fallback

    return text.splitlines()[0]


async def run_command(args, timeout):
    try:
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError:
        return 127, "", f"{args[0]} command not found"

    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout)
    except asyncio.TimeoutError:
        process.kill()
        await process.communicate()
        return 124, "", "timeout"

    return (
        process.returncode,
        stdout.decode(errors="replace"),
        stderr.decode(errors="replace"),
    )


async def ping_command(update, context):
    if not await check_group(update):
        return

    if not context.args or not safe_target(context.args[0]):
        await update.message.reply_text("📘 Usage:\n/ping <host>")
        return

    target = context.args[0]
    returncode, stdout, stderr = await run_command(
        ["ping", "-c", "1", target],
        timeout=3,
    )

    if returncode != 0:
        reason = first_line(stderr or stdout, "unreachable")
        await update.message.reply_text(
            f"❌ Ping failed\n\n"
            f"target: {escape(target)}\n"
            f"reason: {escape(reason)}",
            parse_mode="HTML",
        )
        return

    match = re.search(r"time[=<]([0-9.]+)\s*ms", stdout)
    latency = f"{match.group(1)} ms" if match else "unknown"

    await update.message.reply_text(
        f"📡 Ping result\n\n"
        f"target: {escape(target)}\n"
        f"latency: {escape(latency)}\n"
        f"status: reachable",
        parse_mode="HTML",
    )


async def dns_command(update, context):
    if not await check_group(update):
        return

    if not context.args or not safe_target(context.args[0]):
        await update.message.reply_text("📘 Usage:\n/dns <domain> [record_type]")
        return

    domain = context.args[0]
    record_type = context.args[1].upper() if len(context.args) > 1 else "A"

    if record_type not in DNS_TYPES:
        await update.message.reply_text("⚠️ Supported DNS types: A, AAAA, MX, TXT, NS, CNAME")
        return

    returncode, stdout, stderr = await run_command(
        ["dig", "+short", domain, record_type],
        timeout=3,
    )

    records = [line for line in stdout.splitlines() if line.strip()]
    if returncode != 0 or not records:
        reason = first_line(stderr, "no records found")
        await update.message.reply_text(
            f"❌ DNS lookup failed\n\n"
            f"domain: {escape(domain)}\n"
            f"type: {record_type}\n"
            f"reason: {escape(reason)}",
            parse_mode="HTML",
        )
        return

    await update.message.reply_text(
        f"🌐 DNS lookup\n\n"
        f"domain: {escape(domain)}\n"
        f"type: {record_type}\n\n"
        f"<pre>{escape(trim_output(records))}</pre>",
        parse_mode="HTML",
    )


async def http_command(update, context):
    if not await check_group(update):
        return

    if not context.args or not safe_target(context.args[0]):
        await update.message.reply_text("📘 Usage:\n/http <url>")
        return

    url = context.args[0]
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        await update.message.reply_text("📘 Usage:\n/http <url>")
        return

    timeout = aiohttp.ClientTimeout(total=5)
    start = time.monotonic()

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                status = response.status
                latency = int((time.monotonic() - start) * 1000)
                server = response.headers.get("server", "none")
                content_type = response.headers.get("content-type", "none")
                response.release()

        await update.message.reply_text(
            f"🌐 HTTP check\n\n"
            f"url: {escape(url)}\n"
            f"status: {status}\n"
            f"latency: {latency} ms\n"
            f"server: {escape(server)}\n"
            f"content-type: {escape(content_type)}",
            parse_mode="HTML",
        )

    except Exception as exc:
        await update.message.reply_text(
            f"❌ HTTP check failed\n\n"
            f"reason: {escape(exc)}",
            parse_mode="HTML",
        )


async def whois_command(update, context):
    if not await check_group(update):
        return

    if not context.args or not safe_target(context.args[0]):
        await update.message.reply_text("📘 Usage:\n/whois <domain_or_ip>")
        return

    target = context.args[0]
    returncode, stdout, stderr = await run_command(
        ["whois", target],
        timeout=5,
    )

    lines = [
        line.strip()
        for line in stdout.splitlines()
        if line.strip()
        and not line.lstrip().startswith(("%", "#", ">>>"))
    ]

    if returncode != 0 or not lines:
        reason = first_line(stderr, "no whois data found")
        await update.message.reply_text(
            f"❌ Whois lookup failed\n\n"
            f"target: {escape(target)}\n"
            f"reason: {escape(reason)}",
            parse_mode="HTML",
        )
        return

    await update.message.reply_text(
        f"🌐 Whois result\n\n"
        f"<pre>{escape(trim_output(lines))}</pre>",
        parse_mode="HTML",
    )
