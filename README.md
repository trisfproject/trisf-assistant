<p align="center">
  <img src="assets/banner.png" alt="trisf-assistant banner">
</p>

<p align="center">

<img src="https://img.shields.io/badge/python-3.11+-blue.svg">
<img src="https://img.shields.io/badge/docker-ready-blue.svg">
<img src="https://img.shields.io/badge/license-MIT-green.svg">
<img src="https://img.shields.io/badge/status-active-success.svg">

</p>

# 🤖 trisf-assistant

**trisf-assistant** adalah Telegram group assistant bot untuk **internal tim** yang membantu mengelola shortcut notes, reminder operasional, runbook SOP, todo tracker, dan koordinasi aktivitas langsung dari dalam group.

---

## ✨ Features

* notes shortcut (`/save → /key`)
* reminder scheduler (`/remind`)
* todo tracker (`/todo`)
* runbook SOP (`/runbook`)
* on-call tracker (`/status oncall`)
* AFK status (`/afk`)
* audit log (`/audit`)
* approval-based writer control
* multi-group workspace isolation
* dynamic group whitelist
* Docker-ready deployment

---

## 🚀 Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/trisf-assistant.git
cd trisf-assistant
cp config/.env.example .env
mysql trisf_assistant < sql/schema.sql
docker compose up -d
```

---

## 📚 Documentation

See full guide:

```
docs/documentation.md
```

---

## 🔐 Scope

trisf-assistant dirancang sebagai **internal team assistant bot**, bukan public utility bot.
