from flashcard_clipboard.domain.models import TranslationItem
from flashcard_clipboard.infrastructure.persistence.db import SqliteDB

class FlashcardRepository:
    def __init__(self, db: SqliteDB):
        self.db = db

    def upsert_flashcard(self, item: TranslationItem) -> None:
        sql = """
        INSERT INTO flashcards
          (source_text, translated_text, source_lang, target_lang, captured_at, translated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_text, source_lang, target_lang)
        DO UPDATE SET
          translated_text=excluded.translated_text,
          captured_at=excluded.captured_at,
          translated_at=excluded.translated_at
        ;
        """
        with self.db.connect() as conn:
            conn.execute(
                sql,
                (
                    item.source_text,
                    item.translated_text,
                    item.source_lang,
                    item.target_lang,
                    item.captured_at,
                    item.translated_at,
                ),
            )