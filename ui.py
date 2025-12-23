import pygame
from typing import Optional, Tuple
from movegen import generate_legal_moves, is_in_check
from board import Move, WHITE, BLACK, EMPTY

TILE = 80
MARGIN_TOP = 0
WIDTH = TILE * 8
HEIGHT = TILE * 8 + 80

LIGHT = (235, 236, 208)
DARK  = (119, 149, 86)
HILITE = (246, 246, 105)
CAPTURE = (255, 120, 120)
TEXT = (30, 30, 30)

def load_piece_images(tile_size: int): 
    #use images for pieces
    pieces = {
        1: "wp",  2: "wn",  3: "wb",  4: "wr",  5: "wq",  6: "wk",
       -1: "bp", -2: "bn", -3: "bb", -4: "br", -5: "bq", -6: "bk",
    }

    images = {}
    size = int(tile_size * 0.8)

    for piece, name in pieces.items():
        
        img = pygame.image.load(f"assets/{name}.png").convert_alpha()
        images[piece] = pygame.transform.smoothscale(img, (size, size))

    return images


def sq_to_rc(sq: int) -> Tuple[int, int]:
    return sq // 8, sq % 8

def rc_to_sq(r: int, c: int) -> int:
    return r * 8 + c

def mouse_to_sq(mx: int, my: int) -> Optional[int]:
    if my < 0 or my >= TILE * 8 or mx < 0 or mx >= TILE * 8:
        return None
    c = mx // TILE
    r = my // TILE
    return rc_to_sq(r, c)

def get_game_result(board):
    moves = generate_legal_moves(board)

    if moves:
        return None
    
    if is_in_check(board, board.side_to_move):
        return "checkmate" 
    else:
        return "draw" #stalemate
    
def draw_popup(screen, text, width, height):
    #checkmate and draw screen popup
    overlay = pygame.Surface((width, height))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    box_w, box_h = 420, 160
    box_x = (width - box_w) // 2
    box_y = (height - box_h) // 2

    pygame.draw.rect(
        screen,
        (240, 240, 240),
        (box_x, box_y, box_w, box_h),
        border_radius=10
    )

    pygame.draw.rect(
        screen,
        (40, 40, 40),
        (box_x, box_y, box_w, box_h),
        3,
        border_radius=10
    )

    font = pygame.font.SysFont(None, 36)
    msg = font.render(text, True, (20, 20, 20))
    screen.blit(
        msg,
        (
            box_x + (box_w - msg.get_width()) // 2,
            box_y + (box_h - msg.get_height()) // 2
        )
    )


class ChessUI:
    def __init__(self, board, engine: Optional[object] = None):
        self.board = board
        self.engine = engine

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
    
        self.piece_images = load_piece_images(TILE)
        self.font_ui = pygame.font.SysFont("consolas", 18)

        #drag state
        self.dragging = False
        self.drag_from: Optional[int] = None
        self.drag_piece = EMPTY

        #highlight leagal moves for selected / draged pieces
        self.legal_moves_cache = []
        self.highlight_moves = []

        #ai togle
        self.ai_enabled = False
        self.ai_side = BLACK

        self.game_over = False
        self.game_result = None

    def run(self):
        running = True
        while running:
            self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_u: #undo
                        self.board.undo_move()
                    elif event.key == pygame.K_r: #reset
                        from board import Board
                        self.board = Board.start_position() 
                        self.game_over = False #allows for a board reset when checkmate or draw screen showing
                        self.game_result = None
                    elif event.key == pygame.K_SPACE: #Make AI move
                        self._ai_move_if_needed(force=True)

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._on_mouse_down()

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self._on_mouse_up()

            self._ai_move_if_needed(force=False)

            self.draw()

        pygame.quit()

    def _ai_move_if_needed(self, force: bool):
        if not self.ai_enabled and not force:
            return
        if self.dragging:
            return
        if self.board.side_to_move != self.ai_side and not force:
            return
        if self.board.is_game_over():
            return
        
        move = self.engine.chose_move(self.board)
        if move is not None:
            self.board.make_move(move)
            result = get_game_result(self.board)
            if result:
                self.game_over = True
                self.game_result = result

    def _on_mouse_down(self):
        if self.game_over:
            return
        mx, my = pygame.mouse.get_pos()
        sq = mouse_to_sq(mx, my)
        if sq is None:
            return
        
        piece = self.board.squares[sq]
        if piece == EMPTY:
            return
        if (piece > 0 and self.board.side_to_move != 1) or (piece < 0 and self.board.side_to_move != -1):
            return
        
        self.dragging = True
        self.drag_from = sq
        self.drag_piece = piece

        #cache leagal moves once then filter by from-square for highlighting
        self.legal_moves_cache = generate_legal_moves(self.board)
        self.highlight_moves = [m for m in self.legal_moves_cache if m.from_sq == sq]
        before = self.board.squares.copy()


    def _on_mouse_up(self):
        if not self.dragging:
            return
        
        mx, my = pygame.mouse.get_pos()
        to_sq = mouse_to_sq(mx, my)
        from_sq = self.drag_from

        self.dragging = False
        self.drag_from = None
        self.drag_piece = EMPTY

        if from_sq is None or to_sq is None:
            self.highlight_moves = []
            return
        
        #atempt to find a matching legal move
        for m in self.highlight_moves:
            if m.to_sq == to_sq:
                self.board.make_move(m)
                result = get_game_result(self.board)
                if result:
                    self.game_over = True
                    self.game_result = result
                break

        self.highlight_moves = []

    def _draw_board(self):
        for r in range(8):
            for c in range(8):
                color = LIGHT if (r + c) % 2 == 0  else DARK
                rect = pygame.Rect(c * TILE, r * TILE, TILE, TILE)
                pygame.draw.rect(self.screen, color, rect)

        #highlight target squares for current selected piece
        for m in self.highlight_moves:
            r, c = sq_to_rc(m.to_sq)
            rect = pygame.Rect(c * TILE, r * TILE, TILE, TILE)
            if self.board.squares[m.to_sq] != EMPTY and (self.board.squares[m.to_sq] * self.board.side_to_move) < 0:
                pygame.draw.rect(self.screen, CAPTURE, rect)
            else:
                pygame.draw.rect(self.screen, HILITE, rect)
            #redraw grid
            pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)

    def _draw_pieces(self):
        for sq, piece in enumerate(self.board.squares):
            if piece == EMPTY:
                continue
            #when dragging dont draw on original location
            if self.dragging and self.drag_from == sq:
                continue

            r, c = sq_to_rc(sq)
            self._blit_piece(piece, c * TILE + TILE // 2, r * TILE + TILE // 2)

    def _draw_drag_piece(self):
        if not self.dragging:
            return
        mx, my = pygame.mouse.get_pos()
        self._blit_piece(self.drag_piece, mx, my)
    
    def _blit_piece(self, piece: int, cx: int, cy: int):
        img = self.piece_images.get(piece)
        if img is None:
            return
        rect = img.get_rect(center=(cx, cy))
        self.screen.blit(img, rect)


    def _draw_debug_panel(self):
        #shows on bottom of page to show controls and transposition table size
        y0 = TILE * 8 + 8
        stm = "WHITE" if self.board.side_to_move == WHITE else "BLACK"
        msg = [
            f"Side to move {stm}",
            "Keys: [SPACE] AI move once [U] undo [R] reset",
            f"Zobrist hash: {self.board.zobrist_hash:#016x} | TT size: {self.engine.tt.size()}",

        ]
        for i, line in enumerate(msg):
            surf = self.font_ui.render(line, True, (230, 230, 230))
            self.screen.blit(surf, (8 , y0 + i * 20))

    def draw(self):
        self.screen.fill((20, 20, 20))
        self._draw_board()
        self._draw_pieces()
        self._draw_drag_piece()
        self._draw_debug_panel()

        if self.game_over:
            #popup for checkmake and draw screen
            if self.game_result == "checkmate":
                winner = "Black" if self.board.side_to_move == WHITE else "White"
                draw_popup(self.screen, f"Checkmate! {winner} wins", WIDTH, HEIGHT)
            else:
                draw_popup(self.screen, f"Draw (stalemate)", WIDTH, HEIGHT)

        pygame.display.flip()