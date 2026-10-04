# Changelog

## 1.0.0 — Initial release

The first complete, playable version.

**Game engine (`game.py`)**

- `Card` as a frozen dataclass with a computed value
- `Hand` with `value`, `is_bust`, `is_blackjack` and `is_soft` properties
- `Deck` — a standard 52-card deck, shuffled on construction
- `BlackjackGame` — deals the opening hands, applies player actions, runs
  the dealer, and resolves the outcome
- `GameState` enum driving the round lifecycle
  (`DEALING → PLAYER → DEALER → OVER`)

**Interface (`ui.py`)**

- Dark green table, cards drawn as rounded rectangles with corner ranks and
  a large centre pip
- Dealer hand at the top, player hand at the bottom, both with live totals
- Dealer's hole card drawn face down until the round resolves
- HIT, STAND and NEW GAME buttons with hover states
- Result text centred on the table, coloured per outcome

**Rules implemented**

- Face cards worth 10, Aces worth 11 or 1 with automatic correction
- Blackjack detected on the deal, for either side
- Dealer hits to 17, stands on soft 17
- Win, lose, push and blackjack all handled

**Known limitations**

- No automated test suite
- `Hand.value` and `Hand.is_soft` each contain their own copy of the
  ace-scoring loop
- `dealer_value` reads `dealer_hand.cards[0]` directly and re-scores it,
  duplicating the card-valuation rule
- Round outcomes are plain strings rather than an enum
- Button visibility is decided separately in `draw()` and `handle_events()`
