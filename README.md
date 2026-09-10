# Vestige

A Telegram Business bot that keeps what your chat partner takes back — deleted messages, edited messages, and view-once media.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/manch1915/vestige-bot/ci.yml?branch=main)](https://github.com/manch1915/vestige-bot/actions)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](pyproject.toml)
[![Bot API](https://img.shields.io/badge/Bot%20API-business%20connections-2CA5E0)](https://core.telegram.org/bots/api#businessconnection)

**Русская версия: [README.ru.md](README.ru.md)**

## About

Telegram lets you attach a bot to your personal account through the *Chatbots* section of
your profile. A bot attached that way receives the account's messages — including the
`deleted_business_messages` and `edited_business_message` updates that nothing else on the
platform exposes.

Vestige listens to those updates and reports them back to you in your private chat with
the bot. When someone deletes a message for both of you, you get a copy. When someone
edits one, you get the before and the after. Media is re-sent as a real file, not as a
screenshot of one.

It runs on your own machine. Nothing is uploaded anywhere except into your own Telegram
chat with your own bot.

> **Telegram Premium is not required.** Connecting bots to a personal account used to be a
> Premium feature; it no longer is.

## Features

- **🗑 Deletion alerts** — the moment a message is deleted for both sides, the saved copy
  arrives in your chat with the bot, text and attachment alike.
- **✏️ Edit alerts** — both the old and the new version of an edited message, side by side.
- **🔥 View-once rescue** — reply to a self-destructing photo, video or voice message
  *before* opening it, and it lands in your chat as an ordinary file.
- **⚙️ Settings section** — every alert type is a switch at `t.me/<your-bot>?start=settings`.
  Edit notifications getting noisy? Turn just those off.
- **🌐 Russian and English** interface, switchable from the settings screen.
- **🧹 Retention control** — snapshots expire after `RETENTION_DAYS`, deletion alerts are
  delivered once and then forgotten, and `/purge` wipes everything on demand.

## Requirements

- Python 3.10 or newer (or Docker)
- A bot token from [@BotFather](https://t.me/BotFather) with **Business Mode** enabled

## Installation

```bash
git clone https://github.com/manch1915/vestige-bot.git
cd vestige-bot
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
cp .env.example .env                                 # put your token into BOT_TOKEN
python -m vestige
```

With Docker:

```bash
cp .env.example .env
docker compose up -d
```

## Usage

### 1. Prepare the bot

In [@BotFather](https://t.me/BotFather): `/mybots` → your bot → **Bot Settings** →
**Business Mode** → **Turn on**. Without this the account cannot see your bot in the
Chatbots list.

### 2. Connect it to your account

1. Open your Telegram profile and tap **Edit**
2. Find the **Chatbots** section
3. Enter `@your_bot` and tap **Add**
4. Leave the **read messages** permission enabled — the bot cannot see deletions without it

The bot confirms the connection in your private chat with it. If the read permission is
missing, it says so instead of failing silently.

### 3. Use it

| You want | You do |
| --- | --- |
| Catch deletions and edits | Nothing — it works from the moment you connect |
| Save a view-once file | Reply to it with any message **before** you open it |
| Turn an alert off | `/settings`, or open `t.me/<your-bot>?start=settings` |
| See what is stored | `/status` |
| Erase everything stored | `/purge` |

### What an alert looks like

```
🗑 Deleted message

From: Полина (@polina)
Chat: Полина
Time: 08.01.2026 14:13
Attachment: 🖼 photo

> Любое сообщение
```

The photo itself is attached to that message.

## Configuration

All settings are environment variables, read from `.env` (see [`.env.example`](.env.example)).

| Variable | Default | What it does |
| --- | --- | --- |
| `BOT_TOKEN` | — | Required. Token from @BotFather |
| `DB_PATH` | `data/vestige.db` | SQLite file holding snapshots |
| `MEDIA_DIR` | `data/media` | Where cached media goes |
| `CACHE_MEDIA` | `false` | Download media on arrival instead of relying on `file_id` |
| `MAX_CACHE_FILE_MB` | `20` | Skip caching files larger than this (Bot API download limit) |
| `RETENTION_DAYS` | `14` | Age at which snapshots are dropped; `0` disables cleanup |
| `CLEANUP_INTERVAL_MINUTES` | `60` | How often the janitor runs |
| `LOG_LEVEL` | `INFO` | `DEBUG` when reporting a bug |

**On `CACHE_MEDIA`.** By default Vestige stores only Telegram's `file_id` and re-sends the
file from Telegram's own servers when a deletion happens — cheap, and correct nearly all
the time. Setting `CACHE_MEDIA=true` downloads every file as it arrives, which survives
the case where Telegram invalidates the reference, at the cost of disk space and traffic.

## How it works

Telegram's deletion update carries **ids only** — no text, no files:

```json
{ "business_connection_id": "...", "chat": { ... }, "message_ids": [101, 102] }
```

So the content has to be captured beforehand. Vestige snapshots every message that passes
through the connection into SQLite, and when the deletion update arrives it looks the ids
up and hands the result back to you.

```
business_message         ──▶  capture.py   ──▶  snapshots table
edited_business_message  ──▶  old snapshot  +  new message  ──▶  edit card
deleted_business_messages──▶  pop snapshots by id           ──▶  deletion card
```

| Module | Responsibility |
| --- | --- |
| `handlers/business.py` | The four business updates |
| `handlers/settings.py` | Settings screen and the `?start=settings` deep link |
| `capture.py` | Message → snapshot, with optional media download |
| `storage.py` | SQLite: connections, preferences, snapshots |
| `media.py` | Media extraction, view-once detection, re-sending |
| `render.py` | The notification cards |
| `janitor.py` | Retention sweeps |

View-once detection is deliberately defensive: the Bot API has no documented, stable flag
for self-destructing media, so `media.is_one_time()` checks every known spelling
(`view_once`, `ttl_seconds`, …) on both the message and the media object, reading them out
of aiogram's `model_extra` so a new field name works without a library upgrade. If
Telegram sends no marker at all, the `capture_any_media` preference decides whether to
save the file anyway.

## Privacy

Vestige is a message archive. Read [SECURITY.md](SECURITY.md) before deploying it: it
lists exactly what is written to disk, how long it stays, and how to harden the host.
Recording other people's messages may require their consent where you live.

## Development

```bash
pip install -e ".[dev]"
ruff check . && ruff format --check .
mypy
pytest
```

CI runs the same commands on Python 3.10, 3.11 and 3.12.

## Roadmap

- [ ] Optional forwarding of alerts to a separate "archive" chat or channel
- [ ] Media group (album) handling as a single card
- [ ] Full-text search over stored snapshots
- [ ] Postgres backend for multi-user deployments

## Contributing

Pull requests, bug reports and translations are welcome — see
[CONTRIBUTING.md](CONTRIBUTING.md). By participating you agree to the
[Code of Conduct](CODE_OF_CONDUCT.md).

## Acknowledgments

Built on [aiogram](https://github.com/aiogram/aiogram) and Telegram's
[business connection API](https://core.telegram.org/bots/api#businessconnection). The
feature set is inspired by public chat-automation bots such as @MultiModBot.

## License

Vestige is licensed under the MIT license. See [`LICENSE`](LICENSE) for details.
