# Changelog

## 1.1.0

A cleanup pass over the engine and the UI, plus tests for both.

### Scoring

`Hand.value` and `Hand.is_soft` were each running their own copy of the same
ace loop. Two copies of the rule that decides the score is two chances to get
it wrong, and `is_soft` wasn't being called by anything anyway. Both read from
one `score_cards()` now. `dealer_value` was doing the same thing from the
other direction, reaching into `dealer_hand.cards[0]` and scoring the card
itself, so the engine knew how to score a hand and separately knew how to
value a card. It asks the hand instead.

### Outcomes

Results were bare strings, written in one file and compared in another. A typo
wouldn't have raised anything. It would have fallen through to the `else`
branch and quietly coloured a win as a push. They're a `Result` enum now, so a
misspelling fails at import.

### UI

Which buttons were visible got worked out twice, once to draw them and once to
handle clicks, in two `if/elif` chains that had to stay in step. There's one
`active_buttons()` now. Buttons carry their own action, so click dispatch is a
loop rather than a mapping. The hover handler on mouse-move is gone, because
the draw loop already reads the live mouse position every frame.

### Tests

65 engine checks and 22 UI checks, both runnable with plain Python. Writing
them turned up two things I had wrong. About one deal in ten is an instant
blackjack, which legitimately ends the round on the deal, and my first tests
assumed that never happened.

### Config

Six constants nothing referenced are gone. Eleven values that were sitting
hardcoded in `ui.py` moved into `config.py` with the rest.

## 1.0.0

First working version.

Three files: `game.py` for the rules, `ui.py` for the drawing, `config.py` for
the constants. A full 52-card deck reshuffled each round, aces correcting
themselves between 11 and 1, blackjack detected on the deal, and a dealer that
hits to 17 and stands on soft 17. Win, lose, push and blackjack each get their
own message.

Cards are drawn as rounded rectangles with the rank and suit in the corners
and a large pip in the middle. The dealer's hole card stays face down until
the round resolves. HIT, STAND and NEW GAME buttons with hover states.

No betting, no chips, no sound, no animations, no stats. That was the scope
from the start.
