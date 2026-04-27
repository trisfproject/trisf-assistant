ACCESS_DENIED="❌ You are not allowed to run this command"

WRITE_DENIED="❌ You are not allowed to run this command"

NOTE_NOT_FOUND="⚠️ Note not found"

def GROUP_NOT_ALLOWED(owner):

 return f"""⚠️ This command is not allowed in this group
Contact admin: {owner}
"""
