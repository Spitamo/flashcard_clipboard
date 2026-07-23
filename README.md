# flashcard_clipboard

## Overview

`flashcard_clipboard` is designed for learners and developers who want a fast, lightweight workflow for converting copied text into flashcards. Instead of manually retyping notes into a spaced-repetition tool, this project streamlines the process by using clipboard content as input and transforming it into structured flashcard output.

## Features

- **Clipboard workflow** for rapid capture

- **Extensible architecture** to support custom card formats and pipelines

## Project Structure

```text
flashcard_clipboard/

├─ docs/
│  └─ architecture.md

├─ domain/
│  └─ models.py

├─ infrastructure/
│  ├─ clipboard.py
│  ├─ hotkeys.py
│  ├─ test_hotkeys.py
│  ├─ persistence/
│  │  ├─ db.py
│  │  └─ repository.py
│  └─ translate/
│     ├─ clients.py
│     └─ service.py

├─ pipeline/
│  ├─ app.py
│  ├─ queues.py
│  ├─ stages.py
│  └─ test_stages.py

├─ services/
│  └─ dedup.py

├─ utils/
│  ├─ lru.py
│  └─ text_normalizer.py

├─ .gitignore

├─ config.py

└─ main.py
```
