# trisf-assistant Documentation

Dokumentasi lengkap penggunaan dan deployment **trisf-assistant** sebagai Telegram group assistant bot untuk internal tim.

---

# Overview

trisf-assistant membantu tim operasional menyimpan shortcut knowledge, reminder, runbook SOP, todo tracker, dan koordinasi aktivitas langsung dari Telegram group.

Dirancang untuk:

* Support operations
* Technical community internal

Semua data disimpan berdasarkan:

```
chat_id namespace isolation
```

Sehingga data antar group tidak saling bercampur.

---

# Command Quick Reference

Command utama yang paling sering digunakan:

```
/save key value
/notes
/runbook
/todo
/remind
/health
/status
/audit
/approve
```

---

# Architecture

Flow sederhana:

```
Telegram Group
    ↓
trisf-assistant bot
    ↓
Permission Engine
    ↓
Command Router
    ↓
MySQL Database
```

---

# Project Structure

```
trisf-assistant/
├── app/
├── config/
├── docker/
├── sql/
├── docs/
├── run.py
├── docker-compose.yml
└── requirements.txt
```

---

# Requirements

Minimal environment:

* Docker
* Docker Compose
* MySQL / MariaDB
* Telegram bot token (@BotFather)

---

# Create Telegram Bot

Open Telegram:

```
@BotFather
```

Create bot:

```
/newbot
```

Disable privacy mode:

```
/setprivacy
Disable
```

Required agar bot membaca command di group.

---

# Database Setup

Login MySQL:

```
mysql -u root -p
```

Create database:

```
CREATE DATABASE trisf_assistant;
```

Import schema:

```
mysql trisf_assistant < sql/schema.sql
```

---

# Configuration

Copy config template:

```
cp config/.env.example .env
```

Edit:

```
nano .env
```

Example:

```
BOT_TOKEN=

DB_HOST=
DB_USER=
DB_PASS=
DB_NAME=

SUPERUSER_IDS=12345678

BOT_MODE=restricted

OWNER_CONTACT=@username
```

---

# Run Bot

Start container:

```
docker compose up -d
```

Check logs:

```
docker logs trisf-assistant
```

Expected output:

```
trisf-assistant bot running
```

---

# First-Time Setup in Telegram

Add bot ke group.

Whitelist group:

```
/allowgroup
```

Approve writer pertama:

Reply user message:

```
/approve
```

---

# Permission Model

Hierarchy:

```
SUPERUSER
↓
GROUP ADMIN
↓
APPROVED USER
↓
MEMBER
```

Access matrix:

| Role      | Save Notes | Update/Delete | Allow Group |
| --------- | ---------- | ------------- | ----------- |
| Superuser | ✅          | ✅             | ✅           |
| Admin     | ✅          | ✅             | ❌           |
| Approved  | ✅          | ❌             | ❌           |
| Member    | ❌          | ❌             | ❌           |

---

# Notes Shortcut System

Create shortcut:

```
/save deploy deploy jam 23:00
```

Execute shortcut:

```
/deploy
```

List notes:

```
/notes
```

Update notes:

```
/update deploy deploy jam 22:30
```

Delete notes:

```
/delete deploy
```

---

# Approval System

Approve writer:

Reply message:

```
/approve
```

Approve via user id:

```
/approve 12345678
```

Revoke access:

```
/revoke 12345678
```

List approved users:

```
/approvelist
```

---

# Reminder Scheduler

Examples:

```
/remind 10m restart nginx
/remind 2h deploy staging
/remind 1d backup database
```

Supported units:

```
m = minute
h = hour
d = day
```

Reminder worker berjalan otomatis di background.

---

# Todo Tracker

Add task:

```
/todo cek backup server
```

List tasks:

```
/todo
```

Complete task:

```
/done 1
```

---

# Runbook SOP

Add runbook:

```
/runbook add deployprod git pull && migrate && restart
```

Execute runbook:

```
/runbook deployprod
```

---

# On-Call Tracker

Set on-call user:

```
/oncall @username
```

Check status:

```
/status oncall
```

---

# AFK Status

Set AFK:

```
/afk meeting
```

AFK status otomatis clear saat user mengirim pesan kembali.

---

# Audit Log

View activity:

```
/audit
```

Filter specific key:

```
/audit deployprod
```

Tracks:

* save
* update
* delete
* approve
* revoke
* allowgroup
* import
* export

---

# Export Notes

Backup notes:

```
/export
```

Download JSON file dari Telegram.

---

# Import Notes

Restore notes:

```
/import
```

Upload JSON file hasil export.

---

# Health Check Commands

trisf-assistant menyediakan command monitoring runtime untuk membantu troubleshooting langsung dari Telegram group.

Command ini tersedia untuk:

* superuser
* group admin

---

## /health

Menampilkan status umum bot:

```
/health
```

Contoh output:

```
🤖 trisf-assistant health check

bot: OK
database: OK
scheduler: OK
mode: restricted
uptime: 2h 14m
```

Digunakan untuk memastikan:

* bot berjalan normal
* database reachable
* scheduler aktif
* deployment mode aktif
* runtime uptime

---

## /status bot

Menampilkan runtime status bot:

```
/status bot
```

Contoh output:

```
status: running
uptime: 2h 14m
```

---

## /status db

Menampilkan status koneksi database:

```
/status db
```

Contoh output:

```
database OK (4 ms)
```

Digunakan untuk troubleshooting koneksi database.

---

## /status scheduler

Menampilkan status reminder worker:

```
/status scheduler
```

Contoh output:

```
scheduler running (interval 30s)
```

Digunakan untuk memastikan reminder scheduler aktif.

---

# Group Access Control

Whitelist group:

```
/allowgroup
```

Remove whitelist:

```
/disallowgroup
```

List allowed groups:

```
/groups
```

Superuser only.

---

# Workspace Isolation

Semua data scoped berdasarkan:

```
chat_id
```

Artinya:

* notes group A tidak bisa diakses group B
* todo group A tidak terlihat group lain
* runbook group A tidak terlihat group lain

Database shared, workspace isolated.

---

# Logging

| Type        | Location    |
| ----------- | ----------- |
| Audit log   | MySQL       |
| Runtime log | docker logs |
| Error log   | bot.log     |

---

# Deployment Mode

Restricted mode:

```
BOT_MODE=restricted
```

Hanya group whitelist bisa menggunakan bot.

Open mode:

```
BOT_MODE=open
```

Bot aktif di semua group.

---

# Security Best Practices

Recommended:

* gunakan restricted mode
* set SUPERUSER_IDS
* jangan commit file `.env`
* gunakan database user khusus bot
* gunakan Docker deployment

---

# Docker Commands

Start:

```
docker compose up -d
```

Restart:

```
docker compose restart
```

Stop:

```
docker compose down
```

Logs:

```
docker logs trisf-assistant
```

---

# Troubleshooting

Bot tidak respon command:

Pastikan:

```
privacy mode disabled
```

Database error:

Check:

```
.env config
schema.sql imported
DB reachable
```

Reminder tidak jalan:

Check container logs:

```
docker logs trisf-assistant
```

---

# Usage Scope

trisf-assistant dirancang sebagai:

```
internal team assistant bot
```

bukan:

```
public automation bot
```
