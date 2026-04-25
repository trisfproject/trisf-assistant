import os
from app.db import conn

SUPERUSER_IDS=list(map(int,filter(None,os.getenv("SUPERUSER_IDS","").split(","))))

def is_superuser(uid):
 return uid in SUPERUSER_IDS

def is_writer(chat,user):

 if is_superuser(user):
  return True

 cursor=conn.cursor()

 cursor.execute("""
 SELECT 1 FROM approved_users
 WHERE chat_id=%s AND user_id=%s
 """,(chat,user))

 return cursor.fetchone()!=None