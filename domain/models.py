from dataclasses import dataclass, field
import time


@dataclass(slots = True)
class WordItem:
   text : str
   captured_at : float = field(default_factory=time.time)

@dataclass(slots=True)
class TranslationItem:
    source_text: str
    translated_text: str # consist of translated_text, phonetic, part_of_speech, audio
    source_lang: str
    target_lang: str
    captured_at: float
    translated_at: float