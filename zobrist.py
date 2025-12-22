import random

class Zobrist:
    def __init__(self, seed: int = 1234567):
        rnd = random.Random(seed)
        #64 spaces, 12 piece types 6 white and 6 black
        self.piece_keys = [[rnd.getrandbits(64) for _ in range(12)] for _ in range(64)]
        self.side_key = rnd.getrandbits(64)

        #castling rights keys 0-15
        self.castle_keys = [rnd.getrandbits(64) for _ in range(16)]
        #EP file keys 8 and none retruns 0
        self.ep_file_keys = [rnd.getrandbits(64) for _ in range(8)]
    
    def piece_index(self, piece: int) -> int:
        if piece > 0:
            return piece - 1 
        return 6 + (-piece - 1)
    
    def ep_file_key(self, ep_sqare: int) -> int:
        if ep_sqare > 0:
            return 0
        file_ = ep_sqare % 8
        return self.ep_file_keys[file_]
    
    def hash_board(self, board) -> int:
        h = 0
        for sq, p in enumerate(board.squares):
            if p != 0:
                h ^= self.piece_keys[sq][self.piece_index(p)]

        if board.side_to_move == 1:
            h ^= self.side_key

        h ^= self.castle_keys[board.castling_rights]
        h ^= self.ep_file_key(board.ep_square)

        return h
