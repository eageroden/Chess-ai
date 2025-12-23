from __future__ import annotations
from typing import List

from board import (
    Board, Move, EMPTY,
    PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING,
    WHITE, BLACK, WK, WQ, BK, BQ,
    piece_color, abs_piece
)
# squares are in a 0-63 array each row is 8 squares long so moving down one is 8 sqares
N = -8 #north / up
S = 8 #south / down
E = 1 #east / right
W = -1 #west / left
NW = -9 #up left 
SW = 7 #down left
SE = 9 #down right
NE = -7 #up right

KNIGHT_OFFSETS = (-17, -15, -10, -6, 6, 10, 15, 17) #offsets to move in a L shape 
KING_OFFSETS = (N, S, E, W, NW, SW, SE, NE)

BISHOP_DIRS = (NW, SW, SE, NE) #defines movement of sliding pieces 
ROOK_DIRS = (N, S, E, W)
QUEEN_DIRS = BISHOP_DIRS + ROOK_DIRS #has access to move like bishop and rook

#helpers
#ensures valid indexs
def on_board(sq: int) -> bool:
    return 0 <= sq < 64
#0-7 columns
def file_of(sq: int) -> int:
    return sq & 7

def generate_legal_moves(board: Board) -> List[Move]:
    #full list of leagle moves and check for king in check
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
    #checks if king is in check and must be moved or blocked
    king_sq = board.king_square(color)
    if king_sq is None:
        return False
    return square_attacked(board, king_sq, -color)


def square_attacked(board: Board, sq: int, by_color: int) -> bool:
    #checks if square can be attacked by opponent
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
    #bishop / queen
    for d in BISHOP_DIRS:
        to = sq + d
        while on_board(to) and abs(file_of(to) - file_of(to - d)) == 1:
            p = board.squares[to]
            if p:
                if piece_color(p) == by_color and abs_piece(p) in (BISHOP, QUEEN):
                    return True
                break
            to += d

    #rook / queen
    for d in ROOK_DIRS:
        to = sq + d
        while on_board(to) and (d in (N, S) or abs(file_of(to) - file_of(to - d)) == 1):
            p = board.squares[to]
            if p:
                if piece_color(p) == by_color and abs_piece(p) in (ROOK, QUEEN):
                    return True
                break
            to += d

    #king
    king = KING if by_color == WHITE else -KING
    for d in KING_OFFSETS:
        to = sq + d
        if on_board(to) and board.squares[to] == king:
            if abs(file_of(to) - f) <= 1:
                return True

    return False           

def generate_pseudo_legal_moves(board: Board) -> List[Move]:
    #generates all leagal moves with out checking for any checks
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
    #pawns are difrent becasue they can only move foward but attack sideways 
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

    #Captures and En passant and promotion only to queen as the chance to promote to something else is extremly rare
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
    #used for bishop rook and queen where they can move in a line wether its diagonal or straight or both
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
    #defines where pieces move when castling and checks to make sure they are not attacked squares
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


