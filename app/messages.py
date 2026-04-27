ACCESS_DENIED="🔒 You do not have permission"

WRITE_DENIED="🔒 You do not have permission"

NOTE_NOT_FOUND="⚠️ Note not found"

EMOJI_PREFIXES=(
 "✅",
 "⚠️",
 "❌",
 "ℹ️",
 "📦",
 "📊",
 "📝",
 "👤",
 "👥",
 "🚨",
 "🌙",
 "🔒",
 "📘",
 "⏰",
)


def with_emoji(prefix, text):
 stripped = text.lstrip()
 if stripped.startswith(EMOJI_PREFIXES):
  return stripped

 return f"{prefix} {text}"

def GROUP_NOT_ALLOWED(owner):

 return f"""🔒 This command is not allowed in this group
Contact admin: {owner}
"""
