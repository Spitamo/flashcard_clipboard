from flashcard_clipboard.domain.models import WordItem, TranslationItem
import asyncio
import time


async def translator_worker(
    raw_queue: asyncio.Queue,
    translated_queue: asyncio.Queue,
    translator_service,
    source_lang: str,
    target_lang: str,
):
    while True:
        item: WordItem = await raw_queue.get()
        try:
            translated = await asyncio.to_thread(
                translator_service.translate, item.text, source_lang, target_lang
            )
            if translated:
                out = TranslationItem(
                    source_text=item.text,
                    translated_text=translated,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    captured_at=item.captured_at,
                    translated_at=time.time(),
                )
                await translated_queue.put(out)
        finally:
            raw_queue.task_done()

