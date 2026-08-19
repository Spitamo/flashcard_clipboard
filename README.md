# Flashcard Clipboard

![Python](https://img.shields.io/badge/Python_3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Tauri](https://img.shields.io/badge/Tauri_2-FFC131?style=for-the-badge&logo=tauri&logoColor=black)
![React](https://img.shields.io/badge/React_19-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Rust](https://img.shields.io/badge/Rust-000000?style=for-the-badge&logo=rust&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

## Overview

**Flashcard Clipboard** is a zero-friction desktop vocabulary tool: while reading anything, just select an English word and press `Ctrl+C`. The app automatically reads the clipboard, validates the word, translates it, and saves it as a flashcard — no app-switching, no manual dictionary lookups.

The project is split into two independent parts:

- A **Python backend** that watches the clipboard, processes and translates captured text, persists it to SQLite, and serves it over REST and WebSocket.
- A **Tauri + React desktop UI** that displays new flashcards live and provides a review/study mode.

![Flashcard demo](docs/assets/demo.gif)

## Features

- **Hotkey-driven clipboard capture** — pressing `Ctrl+C` automatically triggers word capture, no manual command required
- **Smart word validation** — filters out URLs, emails, numbers, and non-word text, and checks word "realness" using linguistic frequency (Zipf frequency)
- **Deduplication** via a lightweight LRU cache to avoid reprocessing recently seen words
- **Async, queue-based translation pipeline** with a fallback strategy across two translation services (Google Translate and MyMemory)
- **Persistent SQLite storage** with a unique index to prevent duplicate records and auto-update existing translations
- **Live updates over WebSocket**, with automatic fallback to polling if the connection drops, keeping the UI in sync in real time
- **Desktop UI with two views**:
  - **Feed** — newly captured flashcards in reverse chronological order
  - **Review** — one-at-a-time card review with reveal-to-translate and learned-word tracking

## Architecture

```text
Ctrl+C  ─▶  Hotkey Listener  ─▶  Text Normalizer  ─▶  Dedup (LRU)
                                                          │
                                                          ▼
                                                     Raw Queue
                                                          │
                                                          ▼
                                              Translator Worker
                                          (Google Translate → MyMemory)
                                                          │
                                                          ▼
                                                Translated Queue
                                                          │
                                                          ▼
                                          DB Worker  ─▶  SQLite
                                                          │
                                                          ▼
                                        FastAPI (REST + WebSocket)
                                                          │
                                                          ▼
                                        Tauri / React Desktop UI
```

The backend runs on `asyncio` with two queues so that clipboard capture, translation, and persistence remain independent and non-blocking — pressing the hotkey never waits on a translation service or database write. See [`docs/architecture.md`](docs/architecture.md) for more detail.

## Prerequisites

| Tool | Recommended version |
|---|---|
| Python | 3.10+ |
| Node.js | 20+ |
| pnpm | latest |
| Rust + Cargo | required to build Tauri |

## Running in Development

Start the Python backend first, then launch the Tauri UI in a second terminal.

```bash
# Install dependencies
pip install -r requirements.txt

# Run the backend
python main.py
```

```bash
# In a second terminal
cd tauri-ui
pnpm install
pnpm tauri dev
```

The UI connects to:

- `http://127.0.0.1:51847/flashcards` — initial flashcard list
- `ws://127.0.0.1:51847/ws` — live updates

> In the packaged desktop build, the backend runs as a **sidecar binary** (`binaries/flashcard-backend`) bundled with the app, so `python main.py` doesn't need to be run separately.

## Configuration

Core settings live in `config.py`:

| Key | Default | Description |
|---|---|---|
| `api_port` | `51847` | Port for the FastAPI service |
| `hotkey` | `ctrl+c` | Shortcut used to trigger capture |
| `debounce_sec` | `0.35` | Delay after the hotkey before reading the clipboard |
| `source_lang` / `target_lang` | `en` / `fa` | Translation source/target languages |
| `lru_capacity` | `1024` | Deduplication cache size |
| `http_timeout_sec` | `7.0` | Timeout for translation requests |
| `sqlite_path` | `flashcards.sqlite3` | SQLite database file path |

## Project Structure

```text
flashcard_clipboard/
├─ api.py                          # FastAPI service (REST + WebSocket)
├─ config.py                       # Centralized configuration
├─ main.py                         # App entry point
├─ requirements.txt
├─ docs/
│  └─ architecture.md
│
├─ domain/
│  └─ models.py                    # WordItem and TranslationItem models
│
├─ infrastructure/
│  ├─ clipboard.py                 # System clipboard access
│  ├─ hotkeys.py                   # Hotkey listener running on its own thread
│  ├─ test_hotkeys.py
│  ├─ persistence/
│  │  ├─ db.py                     # SQLite connection and schema
│  │  └─ repository.py             # Flashcard upsert operations
│  └─ translate/
│     ├─ clients.py                # Google Translate and MyMemory clients
│     └─ service.py                # Translation fallback strategy
│
├─ pipeline/
│  ├─ app.py                       # App wiring (workers + server)
│  ├─ queues.py                    # asyncio queues
│  ├─ stages.py                    # Translation and persistence workers
│  └─ test_stages.py
│
├─ services/
│  └─ dedup.py                     # Deduplication service
│
├─ utils/
│  ├─ lru.py                       # LRU cache implementation
│  └─ text_normalizer.py           # Word validation and normalization
│
└─ tauri-ui/                       # Desktop UI
   ├─ package.json
   ├─ src/
   │  ├─ App.tsx                   # Core UI logic (tabs, WS, polling)
   │  └─ App.css
   └─ src-tauri/
      ├─ tauri.conf.json
      └─ src/
         ├─ lib.rs                 # Runs the backend as a sidecar
         └─ main.rs
```

## Desktop UI

The Tauri app has two tabs:

- **Feed** — shows newly captured flashcards in reverse chronological order and animates new arrivals
- **Review** — shows one card at a time, lets you tap to reveal the translation, and tracks which cards you already know via "Skip" and "I know this" buttons

The header shows the connection status to the backend, and the feed falls back to polling automatically if the WebSocket drops, reconnecting live as soon as it's back.

## Testing

```bash
# Backend tests
pytest

# UI tests (if a test script is configured)
cd tauri-ui
pnpm test
```

## Building the Desktop App

```bash
cd tauri-ui
pnpm tauri build
```

## License

This project is licensed under the [MIT License](LICENSE).

---

<p align="center"><b>Contributions are welcome — feel free to join in and help develop this project further </p>