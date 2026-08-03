from domain.models import WordItem, TranslationItem
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
        except Exception as e:
            print(f"[translator] Failed to translate {item.text}: {e}")
        finally:
            raw_queue.task_done()

async def db_worker(
    translated_queue: asyncio.Queue,
    repo,
    notify_fn=None,          
):
    while True:
        item: TranslationItem = await translated_queue.get()
        try:
            await asyncio.to_thread(repo.upsert_flashcard, item)
            print(f"[db] saved: {item.source_text} -> {item.translated_text}")
            if notify_fn:
                try:                                    
                    await notify_fn(                             
                        item.source_text,                         
                        item.translated_text,                    
                        item.captured_at,                        
                    )     
                except Exception as e:
                    print(f"ّ[db] Failed to notify UI {e}")

        except Exception as e:
            print(f"[db] Failed to save flashcard {e}")                                        
        finally:
            translated_queue.task_done()