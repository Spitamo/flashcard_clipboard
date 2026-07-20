from collections import OrderedDict

class LRU:

    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("capacity must be > 0")
        self.capacity = capacity
        self._cache = OrderedDict()

    def seen(self, key: str) -> bool:
        return key in self._cache

    def add(self, key: str) -> bool:
        if key in self._cache:
            # Refresh recency
            # self._cache.move_to_end(key)
            return False

        self._cache[key] = True
        self._cache.move_to_end(key)

        if len(self._cache) > self.capacity:
            self._cache.popitem(last=False)

        return True

    def __contains__(self, key: str) -> bool:
        return key in self._cache

    def items(self):
        return list(self._cache.keys())

