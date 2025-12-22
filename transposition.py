from dataclasses import dataclass
from typing import Optional, Dict
from board import Move

EXACT, LOWER, UPPER = 0, 1, 2

@dataclass
class TTEntry:
    key: int
    depth: int
    score: int
    flag: int
    best_move: Optional[Move]

class TranspositionTable:
    def __init__(self):
        self._table: Dict[int, TTEntry] = {}

    def get(self, key: int) -> Optional[TTEntry]:
        return self._table.get(key)
    
    def store(self, key: int, depth: int, score: int, flag: int, best_move: Optional[Move]):
        prev = self._table.get(key)
        #replace only if deeper or empty 
        if prev is None or depth >= prev.depth:
            self._table[key] = TTEntry(key, depth, score, flag, best_move)

    def size(self) -> int:
        return len(self._table)