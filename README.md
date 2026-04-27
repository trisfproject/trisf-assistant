<p align="center">
  <img src="assets/banner.png" alt="trisf-assistant banner">
</p>

# trisf-assistant

trisf-assistant is a Dockerized Telegram group assistant for internal teams. It provides group-scoped notes, todos, reminders, approvals, group access control, on-call status, AFK notices, backup/restore, and runtime health checks backed by MySQL.

The compose stack starts the bot and MySQL. MySQL initializes from `sql/schema.sql` on first startup.

## Restricted Mode

With `BOT_MODE=restricted`, commands are blocked only when the current chat is not in `allowed_groups` and the user is not listed in `SUPERUSER_IDS`. Superusers can always bootstrap a new group with `/allowgroup`.

## Command Quick Reference

| Area | Commands |
| --- | --- |
| Notes | `/save`, `/update`, `/delete`, `/notes`, `/<key>` |
| Todos | `/todo` |
| Reminders | `/remind` |
| Approvals | `/approve`, `/revoke`, `/approvelist` |
| Group access | `/allowgroup`, `/removegroup`, `/allowedgroups`, `/allowlist`, `/groups` |
| On-call | `/oncall` |
| AFK | `/afk` |
| Audit | `/audit` |
| Backup | `/export`, `/import` |
| Health | `/health`, `/status` |

Full usage guide: [docs/documentation.md](docs/documentation.md)
