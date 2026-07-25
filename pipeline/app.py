import asyncio
import time
import uvicorn

from config import Config
from pipeline.queues import make_queues

from domain.models import WordItem
from services.dedup import DedupService

from pipeline.stages import translator_worker, db_worker
from infrastructure.hotkeys import HotkeyListener
from infrastructure.translate.service import TranslatorService
from infrastructure.persistence.db import SqliteDB
from infrastructure.persistence.repository import FlashcardRepository
from api import notify_new_card  


async def run_app(cfg: Config):
   queues = make_queues(cfg.raw_queue_maxsize, cfg.translated_queue_maxsize)
   dedup = DedupService(cfg.lru_capacity)
   
   translator = TranslatorService(timeout_sec=cfg.http_timeout_sec)
   db = SqliteDB(cfg.sqlite_path)
   repo = FlashcardRepository(db)

   loop = asyncio.get_running_loop()

   def on_word(word: str):
      #called from hotkey thread 
      if not dedup.should_accept(word):
         return
      
      wi = WordItem(text=word, captured_at=time.time())
      loop.call_soon_threadsafe(queues.raw_queue.put_nowait, wi)
      
      print("[dedup] recent:", dedup.recent())

   
   hotkey = HotkeyListener(cfg.hotkey, cfg.debounce_sec, on_word)
   hotkey.start()

   uv_config = uvicorn.Config(
        "api:app",
        host="127.0.0.1",
        port=8000,
        log_level="warning",
    )

   uv_server = uvicorn.Server(uv_config)

   tasks = [
      asyncio.create_task(
         translator_worker(
            queues.raw_queue,
            queues.translated_queue
            ,translator
            ,cfg.source_lang,
            cfg.target_lang
         ),
         name="translator_worker"
      ),
      asyncio.create_task(
         db_worker(
            queues.translated_queue,
            repo,
            notify_fn=notify_new_card,    
         ),
         name="db_worker",
      ),
      asyncio.create_task(
         db_worker(
            queues.translated_queue,
            repo,
            notify_fn=notify_new_card,    
         ),
         name="db_worker",
        ),
        asyncio.create_task(
            uv_server.serve(),                
            name="uvicorn",
        ),
      
   ]

   print("Running on http://127.0.0.1:8000")
   print("Running. Select a word and press Ctrl+C (hotkey).")
   print("To stop the app: focus terminal and press Ctrl+Break or Ctrl+C (terminal interrupt).")

   try:
   #keep the loop alive forever
      while True:
         await asyncio.sleep(424242)
   except KeyboardInterrupt:
      print("Stopping......")

   hotkey.stop()
   for t in tasks:
      t.cancel()
   
   await asyncio.gather(*tasks, return_exceptions=True)