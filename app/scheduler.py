import asyncio
from app.db import conn

async def reminder_worker(app):

 while True:

  cursor=conn.cursor()

  cursor.execute("""
  SELECT id,chat_id,message
  FROM reminders
  WHERE sent=FALSE AND remind_at<=NOW()
  """)

  rows=cursor.fetchall()

  for r in rows:

   await app.bot.send_message(
    r[1],
    f"⏰ Reminder:\n{r[2]}"
   )

   cursor.execute(
    "UPDATE reminders SET sent=TRUE WHERE id=%s",
    (r[0],)
   )

  await asyncio.sleep(30)