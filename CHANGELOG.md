# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2026-09-10

First release.

### Added

- Deletion alerts: a copy of every message the interlocutor deletes, text and media alike.
- Edit alerts: the previous and the current version of an edited message, side by side.
- View-once rescue: replying to a self-destructing file before opening it saves it.
- Settings section reachable at `t.me/<bot>?start=settings` or `/settings`, with a switch
  per notification type and a Russian/English toggle.
- `/status` and `/purge` commands.
- SQLite snapshot storage with a retention janitor and optional media caching to disk.
- Docker image, compose file and a CI workflow across Python 3.10–3.12.

[Unreleased]: https://github.com/manch1915/vestige-bot/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/manch1915/vestige-bot/releases/tag/v0.1.0
