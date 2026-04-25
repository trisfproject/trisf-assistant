ACCESS_DENIED="❌ Anda tidak memiliki hak akses untuk menjalankan perintah ini."

WRITE_DENIED="❌ Anda belum memiliki izin untuk menyimpan notes di grup ini."

NOTE_NOT_FOUND="⚠️ Notes tidak ditemukan. Gunakan /notes."

def GROUP_NOT_ALLOWED(owner):

 return f"""🤖 trisf-assistant

Bot ini digunakan untuk internal tim.

Silakan hubungi {owner} untuk akses penggunaan.
"""