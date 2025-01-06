This example contains a simple Tic-Tac-Toe game. The game is played on a 3x3
grid, where two players take turns to place their marks. The first player to get
three of their marks in a straight line wins the game. You know the rules!

The game has a simple UI with a grid of buttons that represent the game board.
When a player clicks on a button, the corresponding cell is marked with their
symbol. The game checks for a winner after each move and displays a message when
the game is over.

## Lessons 🎓

In this example you can see how to:

- Create and use custom components
- Make components communicate via custom events

## Components 🧩

This example only consists of two components:

1. `Field`: Represents one of the 9 fields on the board. Can contain an `X` or
   an `O`, or be empty.
2. `TicTacToePage`: Represents the entire 3x3 board. This is where the state of
   the board is stored and where the logic for detecting the winner of the game
   is located.
