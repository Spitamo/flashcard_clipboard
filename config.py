from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    api_port: int = 51847
    # Dedup
    lru_capacity: int = 1024

    # Queues
    raw_queue_maxsize: int = 1024          
    translated_queue_maxsize: int = 1024   

    # Translation
    source_lang: str = "en"
    target_lang: str = "fa"
    http_timeout_sec: float = 7.0

    # DB
    sqlite_path: str = "flashcards.sqlite3"

    # Hotkey
    hotkey: str = "ctrl+c"
    debounce_sec: float = 0.35