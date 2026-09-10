# Security policy

## Reporting a vulnerability

Open a [private security advisory](https://github.com/manch1915/vestige-bot/security/advisories/new)
instead of a public issue. Expect a first reply within seven days.

## What this bot stores

Running Vestige means running a message archive. Anyone with access to the machine has
access to the data, so treat the deployment the way you treat your own Telegram session.

| Data | Where | Lifetime |
| --- | --- | --- |
| Text and metadata of messages in connected chats | `DB_PATH` (SQLite) | `RETENTION_DAYS`, or until delivered as a deletion alert |
| Media files, when `CACHE_MEDIA=true` | `MEDIA_DIR` | same |
| Business connection ids and owner ids | `DB_PATH` | until the connection is removed |
| Bot token | `.env` | — |

Nothing is sent anywhere except to the account owner's own chat with the bot.

## Hardening checklist

- Keep `.env` out of version control (it is already in `.gitignore`) and `chmod 600` it.
- Put the database on an encrypted volume — snapshots are stored in plain text.
- Keep `CACHE_MEDIA=false` unless you need it; `file_id` references are enough most of
  the time and cost no disk.
- Lower `RETENTION_DAYS` on shared hosts.
- Revoke the token in @BotFather if the host is ever compromised; that instantly kills
  every business connection.
- `/purge` wipes an owner's snapshots on demand, and disconnecting the bot wipes them
  automatically.

## Legal note

Recording other people's messages may require their consent where you live. You are
responsible for how you use this software.
