from telegram import Update
from telegram.ext import ContextTypes
import random


COFFEE_LEVELS = [
    "CRITICAL",
    "LOW",
    "WARNING",
    "UNKNOWN",
    "RECOVERING",
    "STABLE",
    "HIGH",
    "OVERFLOW",
]

COFFEE_MESSAGES = [
    "brain service still booting... please standby ya ☕",
    "latency turun setelah 1 sip. system looks healthier now.",
    "deploy mood pending caffeine injection.",
    "coffee queue empty. productivity maybe degraded.",
    "lagi sync sama universe dulu bentar.",
    "runtime masih warming up, jangan expect miracles dulu.",
    "cache otak masih cold start.",
    "lagi reconnect ke motivation server...",
    "coffee detected. performance slightly improved.",
    "seems stable, but jangan diajak meeting dulu.",
    "network ke reality agak packet loss dikit.",
    "CPU usage naik setelah americano masuk.",
    "ops mode activated. let's pretend we're productive.",
    "lagi failover ke kopi kedua.",
    "warning: terlalu banyak ide tapi belum ada kopi.",
    "system recovering... kopi udah masuk setengah cup.",
    "coffee pipeline looks healthy.",
    "masih retry connection ke semangat kerja.",
    "deployment mood delayed by sleepy daemon.",
    "coffee overflow detected. proceed with confidence.",
    "looks stable, but jangan sentuh prod dulu ya.",
    "heartbeat normal. caffeine level acceptable.",
    "lagi autoscaling motivation instance.",
    "coffee not found. fallback ke air putih dulu.",
    "service berjalan tapi jiwa belum fully online.",
    "ops vibe detected. siap pura-pura sibuk.",
    "coffee OK. siap menghadapi ticket random.",
    "status unclear but vibes look promising.",
    "coffee synced. brain latency improved.",
    "kayaknya productive, tapi belum tentu.",
    "lagi warming up mental container.",
    "coffee injected. system confidence increased.",
    "masih partial recovery mode.",
    "monitoring mood... looks unstable but operational.",
    "coffee ready. let's ship something risky today.",
    "lagi debugging kehidupan dikit.",
    "runtime stable-ish. proceed carefully.",
    "coffee accepted. anxiety reduced by 3%.",
    "lagi bootstrap energy environment.",
    "container semangat berhasil start ulang.",
]


async def coffee_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    level = random.choice(COFFEE_LEVELS)
    message = random.choice(COFFEE_MESSAGES)

    await update.message.reply_text(
        f"☕ Coffee level: {level}\n{message}"
    )
