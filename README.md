# European-Casino-Roulette

This is a complete, single-file Python script that implements a faithful European Roulette game with:
1. Tkinter Canvas for accurate table layout.
2. Realistic betting zones: Inside (numbers, splits, streets, etc.) and Outside (dozens, columns, colors).
3. Racetrack for Call Bets: Voisins, Tiers, Red/Black Splits, Neighbours.
4. Animated spinning wheel with deceleration and ball drop.
5. Chip-based betting, balance, total bet, Rebet/New Bets/Clear Bet.
6. RTP = 97.3% enforced by correct payouts.

# Key Design Choices:
- table Layout: Grid-based inside bets + labeled outside zones;
- wheel Animation: Uses after() for smooth rotation + ball bounce;
- bet Placement: Click on canvas regions - mapped to bet types;
- call Bets: Predefined chip distributions.

# Features:
- chip stacking;
-smooth wheel animation with easing;
- bet history panel;
- win animations (flashing segment + sparkles);
- real-time statistics tracking (spins, wins, profit, favorite number);
- casino-style graphics;
- no bugs or crashes - thoroughly tested.

# How to Run: 
- python3 European_Casino_Roulette.py
- click numbers or outside zones to place bets;
- use racetrack for Call Bets;
- press SPIN and watch the wheel animate;
- results auto-resolve with correct payouts.

I suppose it’s quite possible to exploit this program as methodical guide for studying of some disciplines «Probability Theory», «Game Theory», «Analytic Combinatorics», «Analysis Algorithms» and «Risk Management». May be this script will help to master the game from scratch in a week and make the learning process fun and exciting. Though we shouldn’t forget the game of real Roulette is associated with financial risks, as the result depends on a random event - the number on which the player has bet.
