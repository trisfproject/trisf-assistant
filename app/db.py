import os
import time
import pymysql
from dotenv import load_dotenv

load_dotenv()


def connect_with_retry():
 attempts = int(os.getenv("DB_CONNECT_RETRIES", "30"))
 delay = int(os.getenv("DB_CONNECT_RETRY_DELAY", "2"))

 for attempt in range(1, attempts + 1):
  try:
   return pymysql.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    database=os.getenv("DB_NAME"),
    autocommit=True,
    connect_timeout=5
   )
  except pymysql.MySQLError:
   if attempt == attempts:
    raise
   time.sleep(delay)


conn=connect_with_retry()
