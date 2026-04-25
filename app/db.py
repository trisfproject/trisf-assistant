import os
import pymysql

conn=pymysql.connect(
 host=os.getenv("DB_HOST"),
 user=os.getenv("DB_USER"),
 password=os.getenv("DB_PASS"),
 database=os.getenv("DB_NAME"),
 autocommit=True
)