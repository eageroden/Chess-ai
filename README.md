# Chess-ai
This is a custom chess engine and graphical interface built from scratch with Python and Pygame. The project is designed with fast move generation with Zobrist hashing and Transposition tables with a simple UI to help with visualization and debugging. I have tested with a 1500 elo bot on chess.com and won in 40 moves, when playing vs a 1800 elo chess bot it got +8 advantage and drew by repetition due to not coding a draw by repetition check in the engine and the engine being deterministic, meaning that for every position only one outcome will ever be made and it will always be the same. my guess is that the chess bot is about 1500 - 1800+ elo on black and slightly worse on white due to the opening not being programed in leading the engine to make worse positions due to not being able to see the payoff of the moves due to the depth not being high enough. 


## Files 
- board.py
Board representation, move making, and undo feature

- engine.py
uses alpha beta pruning for search and orders potential moves with Most Valuable Victim - Least Valuable Aggressor or mvv-lva

- main.py
Entry point of the program

- movegen.py
Fast move generation using array indexing 

- transposition.py
transposition table for hash-based caching with Python dictionary

- ui.py
Pygame user interface 

- zobrist.py
Zobrist hashing implementation to store game state in a 64-bit int


## How to run 
```
pip install pygame
python main.py
```

## Controls 
Drag and drop controls to move pieces
- SPACE : have AI make one move (do not spam this each look up can take some time i tryed to prune as many nodes as posible with the ordering but it still will take some time to get moves 
- U : Undo move can be use multiple times
- R : Resets the game to inital state, can be used on the checkmate or draw screen

## Engine features
- Fast move generation
    - Uses an array-based board representation, for example, if a pawn moves up one square, you simply add +8 or -8, depending on the color of the piece
- Alpha beta pruning with Most Valuable Victim - Least Valuable Aggressor ordering to find the best moves and prune the most nodes in the begining and midgame the depth is set to 5-6, and in the endgame, the depth is higher. This was the best performance to time I was able to find with lower depths, some pawn moves dont payoff, so shuffling pieces looks like risk-free moves to make
- Zobrist Hashing 
    - Unique 64-bit hash for every board position
    - Another option could have been FEN strings witch are stored as human readable tex,t but the sizesare  multiple times larger compared to zobrist hashing witch only takes 8 bytes and allows for integer compare compared to string compare 
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
- No Check popup pieces can't make illegal moves, but there is also no popup for the user
- The engine is pruning lots of nodes but with a depth of 6 the engine can take some time to load the next move
- Engine dosent have openings preprogramed so opening may be unreliable compared to the midgame, as it can take longer than 6 moves to see if an opening is good or not


The chess piece images that are used in this project come from opengameart.org found at this link
https://opengameart.org/content/chess-pieces-and-board-squares
