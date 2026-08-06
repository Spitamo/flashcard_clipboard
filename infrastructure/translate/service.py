from infrastructure.translate.clients import (
    google_translate,
    mymemory_translate,
)

class TranslatorService:
    def __init__(self, timeout_sec: float):
        self.timeout_sec = timeout_sec

    def translate(self, text: str, source_lang: str, target_lang: str) -> str | None:
        # simple fallback strategy
        try:
            
            result = google_translate(text, source_lang, target_lang, timeout=self.timeout_sec)
            if result != text:
                return result
            
            
        except Exception:
            try:
        
                result = mymemory_translate(text, source_lang, target_lang, timeout=self.timeout_sec)
                if result != text:
                    return result
            
            except Exception:
                return None
