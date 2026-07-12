from infrastructure.hotkeys import HotkeyListener as h
from infrastructure.translate.service import TranslatorService as t
import time

translator = t(.3) 

hotkey = h("ctrl+c", 0.30, lambda word : print(f"word : {word} -> {translator.translate(word, 'en', 'fa')}"))

hotkey.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    hotkey.stop()

