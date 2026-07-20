from infrastructure.hotkeys import HotkeyListener as h
from infrastructure.translate.service import TranslatorService as t
from services.dedup import DedupService
import time

lru = DedupService(100)

translator = t(.3) 

def test(word):
    if lru.should_accept(word):
        items = lru.recent()
        print(f'items in LRU {items}')
        return items[-1]


hotkey = h("ctrl+c", 0.30, lambda word : print(f"word : {word} -> {translator.translate(test(word) ,'en', 'fa')}"))

hotkey.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    hotkey.stop()

