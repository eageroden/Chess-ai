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
    #helps avoid evaulation of the same position as you can get the same position with difrent move orders
    #uses dictionary as hash table
    #skips search if exact found
    def __init__(self):
        self._table: Dict[int, TTEntry] = {}

    def get(self, key: int) -> Optional[TTEntry]:
        return self._table.get(key)
    
    def store(self, key: int, depth: int, score: int, flag: int, best_move: Optional[Move]):
        #replace only if deeper or empty
        #deeper searchs are usualy more accurate
        prev = self._table.get(key)
         
        if prev is None or depth >= prev.depth:
            self._table[key] = TTEntry(key, depth, score, flag, best_move)

    def size(self) -> int:
        return len(self._table)