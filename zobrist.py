import random
#used to make 64-bit keys with a seed for debuging when needed
class Zobrist:
    def __init__(self, seed: int = 1234567):
        rnd = random.Random(seed)
        #64 spaces, 12 piece types 6 white and 6 black
        self.piece_keys = [[rnd.getrandbits(64) for _ in range(12)] for _ in range(64)]
        self.side_key = rnd.getrandbits(64) #side to move key

        #castling rights keys 0-15
        #white king side - white queen side - black king side - black queen side
        self.castle_keys = [rnd.getrandbits(64) for _ in range(16)]
        #EP file keys 8 and none retruns 0
        self.ep_file_keys = [rnd.getrandbits(64) for _ in range(8)]
    
    def piece_index(self, piece: int) -> int:
        #pieces 0-11
        if piece > 0:
            return piece - 1 
        return 6 + (-piece - 1)
    
    def ep_file_key(self, ep_square: int) -> int:
        #only depends on file and not rank
        if ep_square == -1:
            return 0
        return self.ep_file_keys[ep_square % 8]
    
    def hash_board(self, board) -> int:
        #gets hash of whole position
        h = 0
        for sq, p in enumerate(board.squares):
            if p != 0:
                h ^= self.piece_keys[sq][self.piece_index(p)]

        if board.side_to_move == 1:
            h ^= self.side_key

        h ^= self.castle_keys[board.castling_rights]
        h ^= self.ep_file_key(board.ep_square)

        return h
