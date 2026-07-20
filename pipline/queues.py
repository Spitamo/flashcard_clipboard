from dataclasses import dataclass
import asyncio

@dataclass(slots = True)
class Queues:
   raw_queue : asyncio.Queue
   translated_queue : asyncio.Queue


def make_queues(raw_maxsize: int = 0, translated_maxsize: int = 0) -> Queues:
    raw_q = asyncio.Queue(maxsize=raw_maxsize)
    tr_q = asyncio.Queue(maxsize=translated_maxsize)
    return Queues(raw_queue=raw_q, translated_queue=tr_q)
    