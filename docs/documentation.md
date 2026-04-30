# trisf-assistant Documentation

**trisf-assistant** is a Telegram assistant bot built for internal team workflows.

It provides shared notes, todos, reminders, approvals, on-call tracking, downtime tracking, and small operational utilities directly inside Telegram, with group data safely scoped by `chat_id` using MySQL.

## Implemented Commands

Current registered command handlers:

```text
/save
/update
/delete
/notes
/approve
/revoke
/approvelist
/promote
/demote
/admins
/del
/purge
/allowgroup
/removegroup
/allowedgroups
/allowlist
/groups
/todo
/remind
/audit
/down
/up
/downlist
/downhistory
/afk
/oncall
/export
/import
/health
/help
/status
/id
/chatid
/ping
/dns
/dns_audit
/http
/whois
/pw
/coffee
/ghost
/pin
/unpin
```

Messages that start with `#` are handled as note lookups. For example, `#deploy` looks for a saved note with key `deploy`.

## Deployment

Copy the environment template and start Docker Compose:

```bash
cp .env.sample .env
nano .env
docker compose up -d
```

`sql/schema.sql` is applied automatically only when MySQL initializes a fresh data directory. For an existing database, apply new schema changes from `sql/migrations/` manually.

Apply the downtime tracking migration:

```bash
docker compose exec -T db mysql -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" < sql/migrations/20260429_add_downtime_events.sql
```

The production layout is expected to be:

```text
/mnt/nfs/docker/trisf-assistant/
├── apps
├── mysql
└── logs
```

`docker-compose.yml` reads `.env` from the repo root, mounts MySQL data at `/mnt/nfs/docker/trisf-assistant/mysql`, and persists bot logs at `/mnt/nfs/docker/trisf-assistant/logs`.

## Configuration

Example `.env`:

```env
BOT_TOKEN=

DB_HOST=db
DB_USER=
DB_PASS=
DB_NAME=trisf_assistant

MYSQL_DATABASE=trisf_assistant
MYSQL_USER=
MYSQL_PASSWORD=
MYSQL_ROOT_PASSWORD=

SUPERUSER_IDS=12345678

BOT_MODE=restricted
OWNER_CONTACT=@trisf
```

`DB_HOST=db` is required for the bot container to connect to the MySQL service in Docker Compose.

## Access Control Model

`SUPERUSER_IDS` is a comma-separated list of Telegram user IDs. Superusers bypass restricted mode and can run superuser-only commands.

Approved users are stored per group in `approved_users`. Approved users can save notes, todos, and reminders in that group.

Allowed groups are stored in `allowed_groups`. In restricted mode, a group must be allowed before normal users can use commands.

Restricted mode blocks a command only when both conditions are true:

```text
chat_id is not in allowed_groups
AND
user_id is not in SUPERUSER_IDS
```

Group admins can run admin commands in allowed groups. Superusers can run privileged commands even before a group is allowed.

## Notes

Create a note directly:

```text
/save key value
```

Save a replied message as a note:

```text
reply to a text message or media caption
/save key
```

Examples:

```text
/save deploy deploy jam 23:00
```

If a user replies to `Kong Production eli...` and sends:

```text
/save kong-prod
```

the note key is `kong-prod` and the note value is the replied message text or caption.

Lookup a note:

```text
#key
```

Use `#note_key` to retrieve saved notes.

List notes:

```text
/notes
```

Update an existing note:

```text
/update key new value
```

Delete a note:

```text
/delete key
```

Notes are stored in a per-group namespace using `chat_id`.

## Todo

List todos for the current group:

```text
/todo
```

Add a todo:

```text
/todo add restart nginx
```

Response:

```text
📝 Todo added
```

Backward-compatible add:

```text
/todo check backup server
```

Mark a todo as completed:

```text
/todo done <id>
/todo complete <id>
```

Delete a todo:

```text
/todo delete <id>
```

Todo list output uses permanent database IDs:

```text
📝 Todo list

#12 restart nginx
#14 check backup cron
```

Todo items use permanent IDs (example: `#12`). IDs remain stable even if other todos are deleted.

`done` marks the todo as completed. `delete` removes the row.

## Reminders

Create reminders:

```text
/remind 10m restart nginx
/remind 2h deploy staging
/remind 1d backup database
```

Supported units are `m`, `h`, and `d`. The scheduler worker sends due reminders in the background.

Reminder scheduling replies mention the requester:

```text
⏰ Reminder scheduled for <user> in 10 minutes
```

Due reminders are sent back to the chat or forum topic where they were created:

```text
⏰ Reminder for <user>

restart nginx
```

## Group Access

Allow the current group:

```text
/allowgroup
```

Remove the current group:

```text
/removegroup
```

List allowed groups:

```text
/allowlist
/groups
/allowedgroups
```

These commands require a superuser.

## Identifier Commands

Show Telegram user information for the current user:

```text
/id
```

Reply to a user message and run:

```text
/id
```

The bot shows information for the replied user.

Username lookup with `/id @username` is not supported by Telegram for regular members. Reply to the user's message and run `/id` instead.

Output format:

```text
👤 User info

id:
username:
name:
is_bot:
```

`username` is shown as `none` if the user has no public username.

Show Telegram chat identifier information:

```text
/chatid
```

In a private chat, the output format is:

```text
👤 Chat info

chat_id:
type:
```

In a group without a topic, the output format is:

```text
👥 Chat info

chat_id:
type:
title:
```

In a forum topic thread, the output format is:

```text
🧵 Topic info

chat_id:
thread_id:
type:
```

`thread_id` only appears when the command is executed inside a forum topic thread.

## Help Menu

Open the interactive inline-button help menu:

```text
/help
```

The menu groups commands by category and includes Back and Done buttons. The Admin category is shown to superusers and Telegram group admins or owners.

Help categories:

```text
📌 Notes
📋 Tasks
📍 Messages
⏰ Reminders
🌐 Network
👤 Info
🧰 Utilities
🔐 Admin
📢 Channel
```

The Admin category includes `/approvelist`, `/audit`, `/export`, and `/import`. Telegram supergroup admins also see `/admins`, `/promote`, `/demote`, `/del`, `/purge`, `/kick`, `/ban`, and `/unban`.

## Network Utility Commands

Check host reachability and latency:

```text
/ping <host>
```

Example:

```text
/ping google.com
```

Response format:

```text
📡 Ping result

target:
latency:
status:
```

Query DNS records:

```text
/dns <domain> [record_type]
```

The default record type is `A`. Supported record types are:

```text
A
AAAA
MX
TXT
NS
CNAME
```

Examples:

```text
/dns google.com
/dns google.com mx
```

Response format:

```text
🌐 DNS lookup

domain:
type:

records
```

Check HTTP endpoint availability:

```text
/http <url>
```

If the URL has no scheme, the bot prepends `https://`.

Response format:

```text
🌐 HTTP check

url:
status:
latency:
server:
content-type:
```

Lookup domain or IP ownership information:

```text
/whois <domain_or_ip>
```

Example:

```text
/whois google.com
```

Response format:

```text
🌐 Whois result

parsed registration info
```

## DNS Audit

Audit a Cloudflare DNS zone:

```text
/dns_audit example.com
```

Exports:

```text
example.com_active.csv
example.com_inactive.csv
```

Audit all Cloudflare zones:

```text
/dns_audit all
```

Exports CSV reports for every zone.

CSV columns:

```text
record
ip
type
status
provider
https_status
```

DNS audit uses HTTPS `HEAD` checks with redirects enabled. If an endpoint rejects `HEAD` with `405`, the bot retries with `GET`. Login redirects where the final URL contains `/login` are treated as active records. Cloudflare-origin errors `521-526`, other `5xx` responses, timeouts, and DNS failures are treated as inactive records.

DNS audit detects infrastructure provider automatically using ASN lookup.

Supported provider detection:

```text
Huawei
GCP
AWS
Azure
Alibaba
Tencent
OCI
Cloudflare
Biznet
Wowrack
DigitalOcean
Linode
```

The `provider` column appears inside exported CSV results, including inactive records that still resolve to an IP address.

Requirements:

```text
CF_API_TOKEN environment variable
cloudflare python SDK
```

Example:

```env
CF_API_TOKEN=xxxxx
```

Permission:

```text
Superuser only
```

Permissions required:

```text
Zone.Zone.Read
Zone.DNS.Read
```

Scope:

```text
All zones
```

## Utility Commands

### /pw

Generate secure password.

Usage:

```text
/pw
/pw 24
```

Default:

```text
16 characters
```

Allowed range:

```text
8-64 characters
```

Charset:

```text
human-safe characters without ambiguous symbols
```

Example:

```text
/pw 20
```

### /coffee

Returns random coffee level status with ops-style witty message.

Usage:

```text
/coffee
```

Example output:

```text
☕ Coffee level: HIGH
deployment mood looks promising today.
```

## Ghost Relay Commands

### /ghost

Send message anonymously through the bot.

Usage:

```text
/ghost deploy production sekarang
```

Or:

```text
reply message + /ghost
```

Requirements:

```text
bot must have delete_messages permission
```

Allowed users:

```text
approved users
group admins
superusers
```

## Message Pinning Commands

Pin or unpin important messages in group chats by replying.

These commands require the bot to be group admin with pin permission enabled.

### /pin

Pin a message in the chat.

Usage:

Reply to a message. By default, `/pin` uses silent mode:

```text
/pin
```

Use loud mode to send a Telegram notification to group members:

```text
/pin loud
```

Example:

```text
(reply to deployment notice)
/pin
```

Response:

```text
📌 Message pinned
```

Permissions:

```text
Approved users
Group admins
Group owners
Superusers
```

### /unpin

Unpin pinned messages in the chat.

Usage:

Default silent mode:

```text
/unpin
```

Use loud mode to send a Telegram notification to group members:

```text
/unpin loud
```

Response:

```text
📍 Message unpinned
```

Permissions:

```text
Approved users
Group admins
Group owners
Superusers
```

If the bot is not admin in the group:

Response:

```text
❌ I need pin permission to do that.
```

## Approval

Approve a user by replying to their message:

```text
/approve
```

Approve by Telegram user ID:

```text
/approve 12345678
```

Revoke approval:

```text
/revoke 12345678
```

List approved users:

```text
/approvelist
```

Approval commands can be run by group admins in allowed groups and by superusers.

## Admin Management Commands

Manage Telegram supergroup administrators.

These commands only work in supergroups. They require the user running the command to already be a Telegram group admin or group owner. Superuser access alone is not enough.

Promote a user as moderator-level admin:

```text
reply to a user message
/promote
```

Or resolve an existing admin by username:

```text
/promote @username
```

Remove admin role:

```text
reply to a user message
/demote
```

Show the current group admin list:

```text
/admins
```

Permissions:

```text
Telegram group admins only
```

The bot must also be a group admin with permission to add new admins.

## Moderation Commands

Promote a user as moderator admin:

```text
reply to a user message
/promote
```

Remove admin role from user:

```text
reply to a user message
/demote
```

Show list of group admins:

```text
/admins
```

Delete a replied message:

```text
reply to a message
/del
```

The bot deletes the replied message and the `/del` command message.

Permissions:

```text
Telegram group admins only
```

The bot must also be a group admin with permission to delete messages.

Delete messages in a range:

```text
reply to the oldest message
/purge
```

The bot deletes messages from the replied message through the `/purge` command message.

Limits:

```text
max 24 hours old
max 200 messages
```

Permissions:

```text
Telegram group admins only
```

Remove a user from the group:

```text
reply to a user message
/kick
```

Ban a user from the group:

```text
reply to a user message
/ban
```

Unban a user:

```text
/unban <user_id>
```

Permissions:

```text
Telegram group admins only
```

## Oncall

Show current on-call user:

```text
/oncall
/oncall status
```

Set on-call user:

```text
/oncall set @username
```

Clear on-call status:

```text
/oncall clear
```

`/oncall` and `/oncall status` are available to everyone in allowed groups. `/oncall set` and `/oncall clear` require a group admin or superuser.

## Downtime Tracking

Track per-group service downtime:

```text
/down service
/down service note about the incident
/up service
/downlist
/downhistory
/downhistory last
/downhistory 7d
/downhistory all
```

`/down <service> [note]` starts an active downtime event for the current group and prevents duplicate active downtime for the same service.

`/up <service>` resolves the active downtime event, records the resolver, and calculates duration.

`/downlist` shows active downtime for the current group.

`/downhistory` shows closed downtime events for the current month by default. Use `last` for last month, `7d` for the last 7 days, or `all` for all closed downtime history.

## AFK

Set global AFK status:

```text
/afk lunch
/afk meeting
/afk driving
```

AFK status is global across all chats. When another user mentions an AFK user or replies to the AFK user's message, the bot replies with the AFK reason and how long the user has been AFK.

When the AFK user sends any new message, the bot clears the AFK status automatically and replies that the user is back.

## Audit

Show recent audit entries for the current group:

```text
/audit
```

Filter by target:

```text
/audit deploy
```

Audit entries are stored per group.

Audit commands require a group admin or superuser.

## Backup

Export current group data:

```text
/export
```

Default export is group-scoped. It exports only the current `chat_id` for notes, todos, reminders, approvals, and on-call status.

Export all groups data:

```text
/export all
```

`/export` and `/import` require a superuser. Operational rule: run full export from a private chat with the bot because it may contain data for multiple groups.

Import a backup:

```text
/import
```

The bot asks for a JSON backup file. Upload the exported JSON document. Import restores rows for the current `chat_id`.

## Health

General health check:

```text
/health
```

Status usage:

```text
/status
```

Database status:

```text
/status db
```

Other implemented status targets:

```text
/status bot
/status scheduler
```

Health and status commands require a group admin or superuser.

## Logging

Runtime logs are written to:

```text
/app/logs/bot.log
```

In Docker deployment, this is mounted to:

```text
/mnt/nfs/docker/trisf-assistant/logs
```

Container logs are still available with:

```bash
docker logs trisf-assistant
```

## Security Notes

Use `BOT_MODE=restricted` for production.

Do not commit `.env`.

Use a dedicated MySQL user for the bot.

Keep `SUPERUSER_IDS` limited to trusted operators.
