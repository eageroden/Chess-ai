from typing import Optional, List
from board import Board, Move, WHITE, BLACK
from movegen import generate_legal_moves, is_in_check
from transposition import TranspositionTable, EXACT, LOWER, UPPER

INF = 10_000_000
MATE_SCORE = 10_000
DRAW_SCORE = 0

# Material values
PIECE_VALUE = {
    1: 100, #pawn
    2: 320, #knight
    3: 330, #bishop
    4: 500, #rook
    5: 900, #queen
    6: 0, #king
}

#Piece square tables from whites perspective
#This helps encourage places that a piece should move twards for exaple knights are more powerfull in the cernter
#of the board becasue they have more spaces to move to compared to the edges 
PAWN_PST = [
    0, 0, 0, 0, 0, 0, 0, 0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5, 5, 10, 25, 25, 10, 5, 5,
    0, 0, 0, 20, 20, 0, 0, 0,
    5, -5, -10, 0, 0, -10, -5, 5,
    5, 10, 10, -20, -20, 10, 10, 5,
    0, 0, 0, 0, 0, 0, 0, 0,
]

KNIGHT_PST = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20, 0, 0, 0, 0, -20, -40,
    -30, 0, 10, 15, 15, 10, 0, -30,
    -30, 5, 15, 20, 20, 15, 5, -30,
    -30, 0, 15, 20, 20, 15, 0, -30,
    -30, 5, 10, 15, 15, 10, 5, -30,
    -40, -20, 0, 5, 5, 0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50
]

BISHOP_PST = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 10, 10, 5, 0, -10,
    -10, 5, 5, 10, 10, 5, 5, -10,
    -10, 0, 10, 10, 10, 10, 0, -10,
    -10, 10, 10, 10, 10, 10, 10, -10,
    -10, 5, 0, 0, 0, 0, 5, -10,
    -20, -10, -10, -10, -10, -10, -10, -20
]

ROOK_PST = [
    0, 0, 0, 0, 0, 0, 0, 0,
    5, 10, 10, 10, 10, 10, 10, 5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    0, 0, 0, 5, 5, 0, 0, 0
]

QUEEN_PST = [
    -20, -10, -10, -5, -5, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 5, 5, 5, 0, -10,
    -5, 0, 5, 5, 5, 5, 0, -5,
    0, 0, 5, 5, 5, 5, 0, -5,
    -10, 5, 5, 5, 5, 5, 0, -10,
    -10, 0, 5, 0, 0, 0, 0, -10,
    -20, -10, -10, -5, -5, -10, -10, -20
]
#adds more king saftey in the mid game
#and allows for more movement in endgames 
KING_PST_MG = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    20, 20, 0, 0, 0, 0, 20, 20,
    20, 30, 10, 0, 0, 10, 30, 20
]
KING_PST_EG = [
    -50, -40, -30, -20, -20, -30, -40, -50,
    -30, -20, -10, 0, 0, -10, -20, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -30, 0, 0, 0, 0, -30, -30,
    -50, -30, -30, -30, -30, -30, -30, -50
]


def is_endgame(board: Board) -> bool:
    #check if we're in endgame phase witch is defined as 2600 in material
    #allows for the king to have more movement in endgames and deeper searchs when less pieces are on the board
    material = 0
    for sq in range(64):
        piece = board.squares[sq]
        if piece != 0 and abs(piece) != 6:
            material += PIECE_VALUE[abs(piece)]
    return material <= 2600


def evaluate(board: Board) -> int:
    # evaluation from perspective of (side to move or stm) Positive is good for side to move negitve if bad for side to move
    score = 0
    endgame = is_endgame(board)
    
    for square in range(64):
        piece = board.squares[square]
        if piece == 0:
            continue
        
        color = WHITE if piece > 0 else BLACK
        piece_type = abs(piece)
        
        #base material value
        value = PIECE_VALUE[piece_type]
        
        #mirror squares for black pieces
        mirror_sq = square if color == WHITE else 63 - square
        
        #piece square table bonus
        pst_bonus = 0
        if piece_type == 1:  #pawn
            pst_bonus = PAWN_PST[mirror_sq]
        elif piece_type == 2:  #knight
            pst_bonus = KNIGHT_PST[mirror_sq]
        elif piece_type == 3:  #bishop
            pst_bonus = BISHOP_PST[mirror_sq]
        elif piece_type == 4:  #rook
            pst_bonus = ROOK_PST[mirror_sq]
        elif piece_type == 5:  #queen
            pst_bonus = QUEEN_PST[mirror_sq]
        elif piece_type == 6:  #king
            pst_bonus = KING_PST_EG[mirror_sq] if endgame else KING_PST_MG[mirror_sq]
        
        piece_score = value + pst_bonus
        
        #score is always baised on side to move
        if color == board.side_to_move:
            score += piece_score
        else:
            score -= piece_score
    
    #Tempo bonus
    score += 10
    
    return score


def mvv_lva_score(board: Board, move: Move) -> int:
    #Most Valuable Victim - Least Valuable Aggressor or mvv-lva 
    #orders captures and queen > pawn over pawn > queen and helps improve alpha beta pruning
    if move.is_ep:
        return 1000  #EP captures are usualy good
    
    victim = board.squares[move.to_sq]
    if victim == 0:
        return 0
    
    attacker = abs(board.squares[move.from_sq])
    return PIECE_VALUE[abs(victim)] - attacker


def order_moves(board: Board, moves: List[Move], tt_move: Optional[Move] = None) -> List[Move]:
    #order moves for better alpha-beta pruning
    if not moves:
        return moves
    
    #separate (transposition tables or tt) move if they exists
    if tt_move and tt_move in moves:
        moves.remove(tt_move)
        ordered = [tt_move]
    else:
        ordered = []
    
    #score remaining moves
    captures = []
    quiet = []
    
    for move in moves:
        if move.is_ep or board.squares[move.to_sq] != 0:
            captures.append((mvv_lva_score(board, move), move))
        else:
            quiet.append(move)
    
    #sort captures by mvv-lva
    captures.sort(reverse=True, key=lambda x: x[0])
    ordered.extend([move for _, move in captures])
    ordered.extend(quiet)
    
    return ordered


class Engine:
    def __init__(self):
        self.nodes = 0
        self.best_move: Optional[Move] = None
        self.tt = TranspositionTable()
        self.max_depth = 6  #Default search depth
    
    def search(self, board: Board, depth: int) -> Optional[Move]:
        #iterative deepening search always keeps best move from deepest completed search
        self.nodes = 0
        self.best_move = None
        
        #extend depth in endgame
        if is_endgame(board):
            depth = min(depth + 2, 8)
        
        # Iterative deepening
        for d in range(1, depth + 1):
            score = self._alphabeta(board, d, -INF, INF, root=True)
        
        return self.best_move
    
    def _alphabeta(
        self,
        board: Board,
        depth: int,
        alpha: int,
        beta: int,
        root: bool = False
    ) -> int:
        #alpha beta search core search used
        
        self.nodes += 1
        alpha_orig = alpha
        
        #transposition table lookup this helps narrow alpha beta window to speed up search
        entry = self.tt.get(board.zobrist_hash)
        if entry and entry.depth >= depth and not root:
            if entry.flag == EXACT:
                return entry.score
            elif entry.flag == LOWER:
                alpha = max(alpha, entry.score)
            elif entry.flag == UPPER:
                beta = min(beta, entry.score)
            if alpha >= beta:
                return entry.score
        
        #leaf node evaluation 
        if depth == 0:
            return self._quiescence(board, alpha, beta, 4)
        
        #move generation
        moves = generate_legal_moves(board)
        
        if not moves:
            if is_in_check(board, board.side_to_move):
                return -MATE_SCORE + (self.max_depth - depth)  #pefers shorter checkmates
            return DRAW_SCORE
        
        #move ordering
        tt_move = entry.best_move if entry else None
        moves = order_moves(board, moves, tt_move)
        
        best_score = -INF
        best_move = None
        
        #search all moves
        for move in moves:
            board.make_move(move)
            score = -self._alphabeta(board, depth - 1, -beta, -alpha)
            board.undo_move()
            
            if score > best_score:
                best_score = score
                best_move = move
            
            alpha = max(alpha, score)
            
            #beta cutoff
            if alpha >= beta:
                break
        
        #store the best move at the root
        if root:
            self.best_move = best_move
        
        #transposition table store
        flag = EXACT
        if best_score <= alpha_orig:
            flag = UPPER
        elif best_score >= beta:
            flag = LOWER
        
        self.tt.store(board.zobrist_hash, depth, best_score, flag, best_move)
        
        return best_score
    
    def _quiescence(self, board: Board, alpha: int, beta: int, depth: int) -> int:
        #helps prevent ustable positions
        #try to search forcing moves like captures
        self.nodes += 1
        
        #stand pat evaluation
        stand_pat = evaluate(board)
        
        if depth == 0:
            return stand_pat
        
        if stand_pat >= beta:
            return beta
        
        if alpha < stand_pat:
            alpha = stand_pat
        
        #only search captures in quiescence
        moves = generate_legal_moves(board)
        captures = [m for m in moves if (m.is_ep or board.squares[m.to_sq] != 0)]
        
        captures.sort(key=lambda m: mvv_lva_score(board, m), reverse=True)
        
        for move in captures:
            board.make_move(move)
            score = -self._quiescence(board, -beta, -alpha, depth - 1)
            board.undo_move()
            
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
        
        return alpha
    
    def chose_move(self, board: Board) -> Optional[Move]:
        #UI entry point
        return self.search(board, depth=5)