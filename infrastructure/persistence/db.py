import sqlite3
from contextlib import contextmanager

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS flashcards (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_text TEXT NOT NULL,
  translated_text TEXT NOT NULL,
  source_lang TEXT NOT NULL,
  target_lang TEXT NOT NULL,
  captured_at REAL NOT NULL,
  translated_at REAL NOT NULL,
  created_at REAL NOT NULL DEFAULT (strftime('%s','now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_flashcards_source_lang
ON flashcards(source_text, source_lang, target_lang);
"""

# connection lifecycle management
class SqliteDB:
   def __init__(self, path: str):
      self.path = path
      self._init()

   @contextmanager
   def connect(self):
      conn = sqlite3.connect(self.path, timeout=10, isolation_level=None)
      try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            yield conn
      finally:
            conn.close()

   def _init(self):
      with self.connect() as conn:
            conn.executescript(SCHEMA_SQL)
