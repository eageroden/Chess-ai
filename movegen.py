from __future__ import annotations
from typing import List

from board import (
    Board, Move, EMPTY,
    PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING,
    WHITE, BLACK, WK, WQ, BK, BQ,
    piece_color, abs_piece
)

N = -8
S = 8
E = 1
W = -1
NW = -9
SW = 7
SE = 9
NE = -7

KNIGHT_OFFSETS = (-17, -15, -10, -6, 6, 10, 15, 17)
KING_OFFSETS = (N, S, E, W, NW, SW, SE, NE)

BISHOP_DIRS = (NW, SW, SE, NE)
ROOK_DIRS = (N, S, E, W)
QUEEN_DIRS = BISHOP_DIRS + ROOK_DIRS

#helpers
def on_board(sq: int) -> bool:
    return 0 <= sq < 64

def file_of(sq: int) -> int:
    return sq & 7

def generate_legal_moves(board: Board) -> List[Move]:
    moves = generate_pseudo_legal_moves(board)
    legal :List[Move] = []
    stm = board.side_to_move

    for m in moves:
        board.make_move(m)
        if not is_in_check(board, stm):
            legal.append(m)
        board.undo_move()

    return legal

def is_in_check(board: Board, color: int) -> bool:
    king_sq = board.king_square(color)
    if king_sq is None:
        return False
    return square_attacked(board, king_sq, -color)


def square_attacked(board: Board, sq: int, by_color: int) -> bool:
    f = file_of(sq)
    #Pawn
    if by_color == WHITE:
        for d in (SW, SE):
            to = sq + d
            if on_board(to) and board.squares[to] == PAWN:
                if abs(file_of(to) - f) == 1:
                    return True
    else:
        for d in (NW, NE):
            to = sq + d
            if on_board(to) and board.squares[to] == -PAWN:
                if abs(file_of(to) - f) == 1:
                    return True
    #knights
    knight = KNIGHT if by_color == WHITE else -KNIGHT
    for d in KNIGHT_OFFSETS:
        to = sq + d
        if on_board(to) and board.squares[to] == knight:
            if abs(file_of(to) - f) <= 2:
                return True
    #BISHOP / QUEEN
    for d in BISHOP_DIRS:
        to = sq + d
        while on_board(to) and abs(file_of(to) - file_of(to - d)) == 1:
            p = board.squares[to]
            if p:
                if piece_color(p) == by_color and abs_piece(p) in (BISHOP, QUEEN):
                    return True
                break
            to += d

    #ROOK / QUEEN
    for d in ROOK_DIRS:
        to = sq + d
        while on_board(to) and (d in (N, S) or abs(file_of(to) - file_of(to - d)) == 1):
            p = board.squares[to]
            if p:
                if piece_color(p) == by_color and abs_piece(p) in (ROOK, QUEEN):
                    return True
                break
            to += d

    #KING
    king = KING if by_color == WHITE else -KING
    for d in KING_OFFSETS:
        to = sq + d
        if on_board(to) and board.squares[to] == king:
            if abs(file_of(to) - f) <= 1:
                return True

    return False           

def generate_pseudo_legal_moves(board: Board) -> List[Move]:
    moves: List[Move] = []
    stm = board.side_to_move

    for sq, piece in enumerate(board.squares):
        if piece == EMPTY or piece_color(piece) != stm:
            continue

        pt = abs_piece(piece)
        f = file_of(sq)

        if pt == PAWN:
            moves.extend(_pawn_moves(board, sq, piece))
        elif pt == KNIGHT:
            for d in KNIGHT_OFFSETS:
                to = sq + d
                if not on_board(to):
                    continue
                if abs(file_of(to) - f) > 2:
                    continue
                if board.squares[to] * stm <= 0:
                    moves.append(Move(sq, to))
        elif pt == BISHOP:
            moves.extend(_slider(board, sq, stm, BISHOP_DIRS))
        elif pt == ROOK: 
            moves.extend(_slider(board, sq, stm, ROOK_DIRS))
        elif pt == QUEEN:
            moves.extend(_slider(board, sq, stm, QUEEN_DIRS))
        elif pt == KING:
            for d in KING_OFFSETS:
                to = sq + d
                if not on_board(to):
                    continue
                if abs(file_of(to) - f) > 1:
                    continue
                if board.squares[to] * stm <= 0: 
                    moves.append(Move(sq, to))
            moves.extend(_castle_moves(board, sq, stm))

    return moves

def _pawn_moves(board: Board, sq: int, pawn: int) -> List[Move]:
    moves: List[Move] = []
    stm = piece_color(pawn)
    f = file_of(sq)

    foward = N if stm == WHITE else S
    start_rank = range(48, 56) if stm == WHITE else range(8, 16)
    promo_rank = range(0, 8) if stm == WHITE else range(56, 64)

    one = sq + foward
    if on_board(one) and board.squares[one] == EMPTY:
        if one in promo_rank:
            moves.append(Move(sq, one, promo=QUEEN))
        else:
            moves.append(Move(sq, one))

        if sq in start_rank:
            two = one + foward
            if board.squares[two] == EMPTY:
                moves.append(Move(sq, two))

    #Captures and EP
    for d in (foward - 1, foward + 1):
        to = sq + d
        if not on_board(to):
            continue
        if abs(file_of(to) - f) != 1:
            continue

        if board.squares[to] * stm < 0:
            if to in promo_rank:
                moves.append(Move(sq, to, promo=QUEEN))
            else:
                moves.append(Move(sq, to))
        elif to == board.ep_square:
            moves.append(Move(sq, to, is_ep=True))

    return moves
    
def _slider(board: Board, sq: int, stm: int, dirs) -> List[Move]:
    moves: List[Move] = []
    f = file_of(sq)

    for d in dirs:
        to = sq + d
        while on_board(to) and (
            d in (N, S) or abs(file_of(to) - file_of(to - d)) == 1
        ):
            p = board.squares[to]
            if p == EMPTY:
                moves.append(Move(sq, to))
            else:
                if piece_color(p) != stm:
                    moves.append(Move(sq, to))
                break
            to += d

    return moves
    
def _castle_moves(board: Board, sq: int, stm: int) -> List[Move]:
    moves: List[Move] = []
    
    if stm == WHITE and sq == 60:
        if board.castling_rights & WK:
            if board.squares[61] == board.squares[62] == EMPTY:
                if not square_attacked(board, 60, BLACK) and \
                    not square_attacked(board, 61, BLACK) and \
                    not square_attacked(board, 62, BLACK):
                        moves.append(Move(60, 62, is_castle=True))
        if board.castling_rights & WQ:
            if board.squares[59] == board.squares[58] == board.squares[57] == EMPTY:
                if not square_attacked(board, 60, BLACK) and \
                    not square_attacked(board, 59, BLACK) and \
                    not square_attacked(board, 58, BLACK):
                        moves.append(Move(60, 58, is_castle=True))
        
    elif stm == BLACK and sq == 4:
        if board.castling_rights & BK:
            if board.squares[5] == board.squares[6] == EMPTY:
                if not square_attacked(board, 4, WHITE) and \
                    not square_attacked(board, 5, WHITE) and \
                    not square_attacked(board, 6, WHITE):
                        moves.append(Move(4, 6, is_castle=True))
        if board.castling_rights & BQ:
            if board.squares[2] == board.squares[3] == board.squares[1] == EMPTY:
                if not square_attacked(board, 4, WHITE) and \
                    not square_attacked(board, 3, WHITE) and \
                    not square_attacked(board, 2, WHITE):
                        moves.append(Move(4, 2, is_castle=True))

    return moves


