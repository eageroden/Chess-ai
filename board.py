from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple

from zobrist import Zobrist 

EMPTY = 0
PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING = 1, 2, 3, 4, 5, 6
WHITE, BLACK = 1,-1

WK, WQ, BK, BQ = 1, 2, 4, 8

def piece_color(piece: int) -> int:
    if piece > 0: return WHITE
    if piece < 0: return BLACK
    return 0

def abs_piece(piece: int) -> int:
    return abs(piece)

@dataclass(frozen=True)
class Move:
    from_sq: int
    to_sq: int
    promo: int = 0 #0 is none, else piece type queen rook bishop knight
    is_ep: bool = False
    is_castle: bool = False

@dataclass
class Undo:
    move: Move
    captured: int
    castling_rights: int
    ep_square: int
    halfmove_clock: int
    fullmove_number: int
    zobrist_hash: int

class Board:
    def __init__(self):
        self.squares: List[int] = [EMPTY] * 64
        self.side_to_move: int = WHITE
        self.castling_rights: int = WK | WQ | BK | BQ
        self.ep_square: int = -1
        self.halfmove_clock: int = 0
        self.fullmove_number: int = 1

        self.zobrist = Zobrist()
        self.zobrist_hash: int = 0

        self.history: List[Undo] = []
    
    @staticmethod
    def start_position() -> "Board":
        b = Board()
        b.squares = [
            -ROOK, -KNIGHT, -BISHOP, -QUEEN, -KING, -BISHOP, -KNIGHT, -ROOK,
            -PAWN, -PAWN, -PAWN, -PAWN, -PAWN, -PAWN, -PAWN, -PAWN,
            0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0,
            PAWN, PAWN, PAWN, PAWN, PAWN, PAWN, PAWN, PAWN,
            ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK
        ]
        b.side_to_move = WHITE
        b.castling_rights = WK | WQ | BK | BQ
        b.ep_square = -1
        b.halfmove_clock = 0
        b.fullmove_number = 1
        b.zobrist_hash = b.zobrist.hash_board(b)
        return b
    
    def king_square(self, color: int) -> int:
        target = KING if color == WHITE else -KING
        for i, p in enumerate(self.squares):
            if p == target:
                return i
        return
    
    def make_move(self, move: Move) -> None:
        #save undo snapshot
        captured = self._get_captured_piece(move)
        undo = Undo(
            move=move, 
            captured=captured,
            castling_rights=self.castling_rights,
            ep_square=self.ep_square,
            halfmove_clock=self.halfmove_clock,
            fullmove_number=self.fullmove_number,
            zobrist_hash=self.zobrist_hash
        )
        self.history.append(undo)

        #zobrist: remove ep, castling, side(we re-add updated) check this
        self.zobrist_hash ^= self.zobrist.side_key
        self.zobrist_hash ^= self.zobrist.castle_keys[self.castling_rights]
        self.zobrist_hash ^= self.zobrist.ep_file_key(self.ep_square)
        
        #clear ep by defult
        self.ep_square = -1 

        moving_piece = self.squares[move.from_sq]

        #haflmove clock reset on pawn move or capture
        if abs_piece(moving_piece) == PAWN or captured != EMPTY:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        #remove moving piece from_sq
        self.zobrist_hash ^= self.zobrist.piece_keys[move.from_sq] [self.zobrist.piece_index(moving_piece)]
        self.squares[move.from_sq] = EMPTY

        #handle capture including ep
        if move.is_ep:
            cap_sq = move.to_sq + (8 if self.side_to_move == WHITE else -8)
            cap_piece = self.squares[cap_sq]
            self.zobrist_hash ^= self.zobrist.piece_keys[cap_sq][self.zobrist.piece_index(cap_piece)]
            self.squares[cap_sq] = EMPTY
        elif captured != EMPTY:
            self.zobrist_hash ^= self.zobrist.piece_keys[move.to_sq][self.zobrist.piece_index(captured)]

        #handle castling rook move
        if move.is_castle:
            self._do_castle_rook(move)

        #place piece (promotion also handled here)
        placed_piece = moving_piece
        if move.promo != 0:
            placed_piece = move.promo if self.side_to_move == WHITE else -move.promo

        self.squares[move.to_sq] = placed_piece
        self.zobrist_hash ^= self.zobrist.piece_keys[move.to_sq][self.zobrist.piece_index(placed_piece)]

        #update castling rights if king or rook moved or rook captured
        self._update_castling_rights(move, moving_piece, captured)

        #set EP square if pawn moves up 2
        if abs_piece(moving_piece) == PAWN and abs(move.to_sq - move.from_sq) == 16:
            self.ep_square = (move.from_sq + move.to_sq) // 2

        #move number
        if self.side_to_move == BLACK:
            self.fullmove_number += 1

        #switch side 
        self.side_to_move *= -1

        #zobrist add new ep/castling 
        self.zobrist_hash ^= self.zobrist.castle_keys[self.castling_rights]
        self.zobrist_hash ^= self.zobrist.ep_file_key(self.ep_square)
    
    def undo_move(self) -> None:
        if not self.history:
            return

        u = self.history.pop()
        move = u.move

        self.zobrist_hash = u.zobrist_hash
        self.castling_rights = u.castling_rights
        self.ep_square = u.ep_square
        self.halfmove_clock = u.halfmove_clock
        self.fullmove_number = u.fullmove_number

        self.side_to_move *= -1

        moved_piece = self.squares[move.to_sq]

        if move.is_castle:
            self._undo_castle_rook(move)

        if move.promo != 0:
            moved_piece = PAWN if self.side_to_move == WHITE else -PAWN

        self.squares[move.to_sq] = EMPTY

        self.squares[move.from_sq] = moved_piece

        if move.is_ep:
            cap_sq = move.to_sq + (8 if self.side_to_move == WHITE else -8)
            self.squares[cap_sq] = u.captured
        else:
            self.squares[move.to_sq] = u.captured


    def _do_castle_rook(self, move: Move) -> None:
        #king moved to_sq identifies which castle it was 
        #White: e1->g1 king rook h1->f1, e1->c1 king rook a1->d1
        #Black: e8->g8 king  rook h8->f8, e8->c8 king rook a8->d8
        if move.to_sq == 62: #white king side
            self._move_rook(63, 61)
        elif move.to_sq == 58: #white queen side
            self._move_rook(56, 59)
        elif move.to_sq == 6: #black king side
            self._move_rook(7, 5)
        elif move.to_sq == 2: #black queen side
            self._move_rook(0, 3)
    
    def _undo_castle_rook(self, move: Move) -> None:
        if move.to_sq == 62:
            self.squares[63] = self.squares[61]; self.squares[61] = EMPTY
        elif move.to_sq == 58:
            self.squares[56] = self.squares[59]; self.squares[59] = EMPTY
        elif move.to_sq == 6:
            self.squares[7] = self.squares[5]; self.squares[5] = EMPTY
        elif move.to_sq == 2:
            self.squares[0] = self.squares[3]; self.squares[3] = EMPTY

    def _move_rook(self, from_sq: int, to_sq: int) -> None:
        rook = self.squares[from_sq]
        #update zobrist
        self.zobrist_hash ^= self.zobrist.piece_keys[from_sq][self.zobrist.piece_index(rook)]
        self.zobrist_hash ^= self.zobrist.piece_keys[to_sq][self.zobrist.piece_index(rook)]
        self.squares[from_sq] = EMPTY
        self.squares[to_sq] = rook

    def _get_captured_piece(self, move: Move) -> int:
        if move.is_ep:
            cap_sq = move.to_sq + (8 if self.side_to_move == WHITE else -8)
            return self.squares[cap_sq]
        return self.squares[move.to_sq]


    def _update_castling_rights(self, move, moving_piece: int, captured: int) -> None:
        #removes ability to castle on a given side if rook moves or is taken or a king moves
        #king moves
        if abs_piece(moving_piece) == KING:
            if self.side_to_move == WHITE:
                self.castling_rights &= ~(WK | WQ)
            else:
                self.castling_rights &= ~(BK | BQ)
            
        #rook moves
        if abs_piece(moving_piece) == ROOK:
            if move.from_sq == 63: self.castling_rights &= ~WK
            if move.from_sq == 56: self.castling_rights &= ~WQ
            if move.from_sq == 7: self.castling_rights &= ~BK
            if move.from_sq == 0: self.castling_rights &= ~BQ
        
        #rook captured on original square
        if abs_piece(captured) == ROOK:
            if move.to_sq == 63: self.castling_rights &= ~WK
            if move.to_sq == 56: self.castling_rights &= ~WQ
            if move.to_sq == 7: self.castling_rights &= ~BK
            if move.to_sq == 0: self.castling_rights &= ~BQ

    def is_game_over(self) -> bool:
        from movegen import generate_legal_moves
        if generate_legal_moves(self):
            return False
        #no legal moves mean checkmate or stalemate
        return True