import time
import threading
import keyboard

from clipboard import get_clipboard

class HotkeyListener:
    """
    Listens to a hotkey (e.g. ctrl+c). When pressed:
      - waits debounce
      - reads clipboard
      
    Runs keyboard hook in a background thread so asyncio loop can be the main thread.
    """
    def __init__(self, hotkey: str, debounce_sec: float):
        self.hotkey = hotkey
        self.debounce_sec = debounce_sec
        

        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self):
        if self._thread and self._thread.is_alive():
            return

        def _run():
            def _handler():
                # Let OS update clipboard after Ctrl+C
                time.sleep(self.debounce_sec)
                print(get_clipboard())
                

            keyboard.add_hotkey(self.hotkey, _handler)
            print(f"[hotkey] registered: {self.hotkey}")
            # Keep this thread alive until stop
            while not self._stop.is_set():
                time.sleep(0.1)

            try:
                keyboard.remove_hotkey(self.hotkey)
            except Exception:
                pass

        self._thread = threading.Thread(target=_run, name="hotkey-listener", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()