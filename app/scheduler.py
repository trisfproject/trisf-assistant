import asyncio
import html
import json
import logging

from app.db import conn

logger = logging.getLogger(__name__)


def requester_mention(requester):
 user_id = requester.get("id")
 full_name = requester.get("full_name") or str(user_id)

 return f'<a href="tg://user?id={user_id}">{html.escape(full_name)}</a>'


def parse_reminder_payload(raw_message, user_id):
 try:
  payload = json.loads(raw_message)
 except (TypeError, json.JSONDecodeError):
  return {
   "text": raw_message,
   "requester": {
    "id": user_id,
    "full_name": str(user_id),
   },
   "thread_id": None,
  }

 if not isinstance(payload, dict):
  return {
   "text": raw_message,
   "requester": {
    "id": user_id,
    "full_name": str(user_id),
   },
   "thread_id": None,
  }

 requester = payload.get("requester") or {}
 if not requester.get("id"):
  requester["id"] = user_id
 if not requester.get("full_name"):
  requester["full_name"] = str(requester["id"])

 return {
  "text": payload.get("text") or "",
  "requester": requester,
  "thread_id": payload.get("thread_id"),
 }


async def reminder_worker(app):

 try:
  while True:

   try:
    cursor=conn.cursor()

    cursor.execute("""
    SELECT id,chat_id,user_id,message
    FROM reminders
    WHERE sent=FALSE AND remind_at<=NOW()
    """)

    rows=cursor.fetchall()

   except Exception:
    logger.exception("failed to fetch due reminders")

   else:
    for r in rows:

     try:
      reminder = parse_reminder_payload(r[3], r[2])
      send_kwargs = {
       "chat_id": r[1],
       "text": (
        f"⏰ Reminder for {requester_mention(reminder['requester'])}\n\n"
        f"{html.escape(reminder['text'])}"
       ),
       "parse_mode": "HTML",
      }

      if reminder["thread_id"]:
       send_kwargs["message_thread_id"] = reminder["thread_id"]

      await app.bot.send_message(
       **send_kwargs
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

 except asyncio.CancelledError:
  logger.info("reminder worker stopped")
  raise
