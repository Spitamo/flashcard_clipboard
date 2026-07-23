from utils.lru import LRU

class DedupService:
   def __init__(self, capacity):
      self.lru = LRU(capacity)

   def should_accept(self, word: str) -> bool:
      # if True --> new word
      return self.lru.add(word)

   def recent(self):
      return self.lru.items()