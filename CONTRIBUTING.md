# Contributing

Thanks for taking the time. Bug reports, translations and pull requests are all welcome.

## Development setup

```bash
git clone https://github.com/manch1915/vestige-bot.git
cd vestige-bot
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env           # then put your token in
```

Run the bot with `python -m vestige`.

## Before opening a pull request

```bash
ruff check .
ruff format .
mypy
pytest
```

CI runs the same four commands on Python 3.10, 3.11 and 3.12.

## Conventions

- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/):
  `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`.
- Handlers stay thin — put logic in `capture.py`, `storage.py` or `render.py` so it can
  be tested without a Telegram connection.
- New user-facing strings go into **both** `RU` and `EN` in `src/vestige/texts.py`.
- A new preference needs an entry in `PREF_KEYS`, a column in the `prefs` table and a
  `pref_<key>` string in both locales.

## Adding a language

Copy the `EN` dictionary in `src/vestige/texts.py`, translate the values, register it in
`LANGUAGES`. The language button in `/settings` cycles through everything registered there.

## Reporting bugs

Include the Bot API error text if there is one, the update type involved
(`business_message`, `deleted_business_messages`, …) and your Python version. Never paste
your bot token — regenerate it in @BotFather if it leaks.
