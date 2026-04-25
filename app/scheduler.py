import asyncio
import logging

from app.db import conn

logger = logging.getLogger(__name__)


async def reminder_worker(app):

 while True:

  try:
   cursor=conn.cursor()

   cursor.execute("""
   SELECT id,chat_id,message
   FROM reminders
   WHERE sent=FALSE AND remind_at<=NOW()
   """)

   rows=cursor.fetchall()

  except Exception:
   logger.exception("failed to fetch due reminders")

  else:
   for r in rows:

    try:
     await app.bot.send_message(
      r[1],
      f"⏰ Reminder:\n{r[2]}"
     )

     cursor.execute(
      "UPDATE reminders SET sent=TRUE WHERE id=%s",
      (r[0],)
     )

    except Exception:
     logger.exception(
      "failed to send reminder id=%s chat_id=%s",
      r[0],
      r[1],
     )

  await asyncio.sleep(30)
