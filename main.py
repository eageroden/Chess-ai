import pygame
from ui import ChessUI
from board import Board
from engine import Engine

def main():
    pygame.init()
    pygame.display.set_caption("Chess AI")

    board = Board.start_position()
    engine = Engine()

    ui = ChessUI(board=board, engine=engine)
    ui.run()

if __name__ == "__main__":
    main()