# Chess-ai
This is a custom chess engine and graphical interface built from scratch with Python and Pygame. The project is designed with fast move generation with Zobrist hashing and Transposition tables with a simple UI to help with visulization and debuging.

## Files 
- board.py
Board repersentation, move making, and undo feature

- engine.py
WIP currently 

- main.py
Entry point of program

- movegen.py
Fast move generation using array indexing 

- transposition.py
transposition table for hash baised caching

- ui.py
Pygame user interface 

- zobrist.py
Zobrist hashing implmentation


## How to run 
```
pip install pygame
python main.py
```

## Controls 
Drag and drop controls to move pieces
A : toggle AI
SPACE : have AI make one move
U : Undo move can be use multiple times
R : Resets game to inital state

## Engine featues
- Fast move generation
    - Uses an array baised board repersentaion for example if a pawn moves up one square you simply add +8 or -8 depending on the color of the piece
- Zobrist Hashing 
    - Unique 64-bit hash for every board posiotion
    - Another option could have been FEN strings witch are stored as human redable text but the sizes multiple times larger compared to zobrist hashing witch only takes 8 bytes and allows for integer compare compared to string compare 
    - Includes 
        - piece placement 
        - Whos move it is
        - Who can still castle
        - En passant files 
- Transposition Table
    - Caches previously evaluated position as Zobrist hashes
    - Avoids re-searching indentical board states (multiple move orders can end up in the same position this allow the program to remove the unneeded searches of the same position)
    - Stores
        - Depth
        - Score
        - Node type (exact/lower/upper)
        - Best move
- Undo system
    - Full move undo support
    - Can restore 
        - Board 
        - castling rights
        - En passant
        - Zobrist hashing

## Current Limitations 
- No Checkmate UI popup yet
- Engine WIP


The chess piece images that are used in this project come from opengameart.org found at this link
https://opengameart.org/content/chess-pieces-and-board-squares
