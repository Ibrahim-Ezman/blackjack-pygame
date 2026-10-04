"""
Test suite for the Blackjack game engine (game.py).

Runs with plain Python — no pytest required:

    python test_game.py

Exits with status 1 if any check fails, so it can be wired into CI.

These tests cover the rules that are easy to get wrong: soft-ace
correction, blackjack detection, the dealer stand-on-17 rule, and
the win/lose/push decision tree.
"""

from game import (
    BlackjackGame,
    Card,
    Deck,
    GameState,
    Hand,
    Result,
    score_cards,
)

_failures: list[str] = []
_checks = 0


def check(label: str, condition: bool) -> None:
    """Record and report a single assertion."""
    global _checks
    _checks += 1
    if condition:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label}")
        _failures.append(label)


def make_hand(*specs: tuple[str, str]) -> Hand:
    """Build a Hand from ('A', 'Spades')-style tuples."""
    hand = Hand()
    for rank, suit in specs:
        hand.add(Card(rank, suit))
    return hand


def controlled_game(
    player_specs: tuple[tuple[str, str], ...],
    dealer_specs: tuple[tuple[str, str], ...],
    remaining: tuple[tuple[str, str], ...] = (),
) -> BlackjackGame:
    """
    Build a game with fixed hands and a rigged deck.

    Deck.deal() uses list.pop(), which removes from the END of the
    list — so the LAST card in `remaining` is dealt first.
    """
    game = BlackjackGame()
    game.player_hand.clear()
    game.dealer_hand.clear()
    for rank, suit in player_specs:
        game.player_hand.add(Card(rank, suit))
    for rank, suit in dealer_specs:
        game.dealer_hand.add(Card(rank, suit))
    game.deck.cards = [Card(rank, suit) for rank, suit in remaining]
    game.state = GameState.PLAYER
    game.dealer_revealed = False
    game.result = None
    game.result_message = ""
    return game


def resolved(
    player_specs: tuple[tuple[str, str], ...],
    dealer_specs: tuple[tuple[str, str], ...],
) -> BlackjackGame:
    """Build a game with fixed hands and settle the round immediately."""
    game = controlled_game(player_specs, dealer_specs)
    game._finish_round()
    return game


# ---------------------------------------------------------------------------
# Deck
# ---------------------------------------------------------------------------

def test_deck() -> None:
    deck = Deck()
    check("deck has 52 cards", len(deck) == 52)

    unique = {(c.rank, c.suit) for c in deck.cards}
    check("deck has 52 unique rank/suit pairs", len(unique) == 52)

    check(
        "deck contains all 4 suits",
        {c.suit for c in deck.cards} == {"Hearts", "Diamonds", "Clubs", "Spades"},
    )

    deck = Deck()
    deck.deal()
    check("deal() removes a card from the deck", len(deck) == 51)


# ---------------------------------------------------------------------------
# Scoring — soft ace handling
# ---------------------------------------------------------------------------

def test_scoring() -> None:
    check("number cards use face value", make_hand(("7", "Clubs")).value == 7)
    check("face cards are worth 10", make_hand(("J", "Clubs"), ("Q", "Hearts")).value == 20)
    check("king is worth 10", make_hand(("K", "Clubs")).value == 10)

    # Ace counted as 11 when it does not bust the hand
    check("A + K = 21 (ace high)", make_hand(("A", "Spades"), ("K", "Hearts")).value == 21)

    # Ace demoted to 1 to stay under 21
    check("A + 9 + 5 = 15 (ace demoted)", make_hand(("A", "Spades"), ("9", "Hearts"), ("5", "Clubs")).value == 15)

    # Two aces: one high, one low
    check("A + A = 12", make_hand(("A", "Spades"), ("A", "Hearts")).value == 12)
    check("A + A + 9 = 21", make_hand(("A", "Spades"), ("A", "Hearts"), ("9", "Clubs")).value == 21)

    # An ace cannot save a busted hand
    check("K + Q + A = 21", make_hand(("K", "Spades"), ("Q", "Hearts"), ("A", "Clubs")).value == 21)
    check("K + Q + 5 = 25 (bust)", make_hand(("K", "Spades"), ("Q", "Hearts"), ("5", "Clubs")).value == 25)

    check("empty hand scores 0", make_hand().value == 0)


def test_score_cards_helper() -> None:
    total, aces_high = score_cards([Card("A", "Spades"), Card("K", "Hearts")])
    check("score_cards total for A+K", total == 21)
    check("score_cards counts 1 ace high", aces_high == 1)

    total, aces_high = score_cards([Card("A", "Spades"), Card("9", "Hearts"), Card("5", "Clubs")])
    check("score_cards demotes ace when busting", (total, aces_high) == (15, 0))

    total, aces_high = score_cards([Card("A", "Spades"), Card("A", "Hearts")])
    check("score_cards keeps one ace high", (total, aces_high) == (12, 1))


def test_soft_flag() -> None:
    check("A + 6 is soft", make_hand(("A", "Spades"), ("6", "Hearts")).is_soft)
    check("A + 9 + 5 is hard (ace demoted)", not make_hand(("A", "Spades"), ("9", "Hearts"), ("5", "Clubs")).is_soft)
    check("K + 7 is hard", not make_hand(("K", "Spades"), ("7", "Hearts")).is_soft)


def test_blackjack_detection() -> None:
    check("A + K is blackjack", make_hand(("A", "Spades"), ("K", "Hearts")).is_blackjack)
    check("10 + A is blackjack", make_hand(("10", "Spades"), ("A", "Hearts")).is_blackjack)
    check(
        "21 with three cards is NOT blackjack",
        not make_hand(("7", "Spades"), ("7", "Hearts"), ("7", "Clubs")).is_blackjack,
    )
    check("20 is not blackjack", not make_hand(("10", "Spades"), ("K", "Hearts")).is_blackjack)


# ---------------------------------------------------------------------------
# Dealer AI
# ---------------------------------------------------------------------------

def test_dealer_stands_on_17() -> None:
    game = controlled_game((("K", "Spades"), ("9", "Hearts")), (("10", "Clubs"), ("7", "Diamonds")))
    game.stand()
    check("dealer stands at hard 17", len(game.dealer_hand) == 2)
    check("dealer total is 17", game.dealer_value == 17)
    check("player 19 beats dealer 17", game.result is Result.WIN)


def test_dealer_stands_on_soft_17() -> None:
    # A + 6 = soft 17: the dealer must stand (standard rule, no hit).
    game = controlled_game((("K", "Spades"), ("9", "Hearts")), (("A", "Clubs"), ("6", "Diamonds")))
    game.stand()
    check("dealer stands on soft 17", len(game.dealer_hand) == 2)
    check("dealer total is 17", game.dealer_value == 17)


def test_dealer_hits_below_17() -> None:
    game = controlled_game(
        (("K", "Spades"), ("9", "Hearts")),
        (("5", "Clubs"), ("6", "Diamonds")),
        remaining=(("10", "Spades"),),   # dealt first (pop takes from the end)
    )
    game.stand()
    check("dealer draws to reach 17+", len(game.dealer_hand) == 3)
    check("dealer total is 21", game.dealer_value == 21)
    check("dealer 21 beats player 19", game.result is Result.LOSE)


def test_dealer_busts() -> None:
    game = controlled_game(
        (("K", "Spades"), ("9", "Hearts")),
        (("6", "Clubs"), ("6", "Diamonds")),
        remaining=(("10", "Spades"),),   # 12 + 10 = 22
    )
    game.stand()
    check("dealer busts at 22", game.dealer_hand.is_bust)
    check("player wins when dealer busts", game.result is Result.WIN)


# ---------------------------------------------------------------------------
# Round resolution
# ---------------------------------------------------------------------------

def test_resolution() -> None:
    check("player 20 beats dealer 19", resolved((("K", "Spades"), ("Q", "Hearts")), (("10", "Clubs"), ("9", "Diamonds"))).result is Result.WIN)
    check("player 19 loses to dealer 20", resolved((("10", "Spades"), ("9", "Hearts")), (("K", "Clubs"), ("Q", "Diamonds"))).result is Result.LOSE)
    check("equal totals push", resolved((("10", "Spades"), ("9", "Hearts")), (("K", "Clubs"), ("9", "Diamonds"))).result is Result.PUSH)
    check("player bust loses", resolved((("K", "Spades"), ("Q", "Hearts"), ("5", "Clubs")), (("10", "Clubs"), ("9", "Diamonds"))).result is Result.LOSE)
    check("dealer bust wins for player", resolved((("10", "Spades"), ("9", "Hearts")), (("K", "Clubs"), ("Q", "Diamonds"), ("5", "Clubs"))).result is Result.WIN)

    check("player blackjack wins", resolved((("A", "Spades"), ("K", "Hearts")), (("10", "Clubs"), ("9", "Diamonds"))).result is Result.BLACKJACK)
    check("dealer blackjack loses", resolved((("10", "Spades"), ("9", "Hearts")), (("A", "Clubs"), ("K", "Diamonds"))).result is Result.LOSE)
    check("both blackjack pushes", resolved((("A", "Spades"), ("K", "Hearts")), (("A", "Clubs"), ("Q", "Diamonds"))).result is Result.PUSH)

    # 21 in three cards is a normal win, not a blackjack
    check("three-card 21 is a plain win", resolved((("7", "Spades"), ("7", "Hearts"), ("7", "Clubs")), (("10", "Clubs"), ("9", "Diamonds"))).result is Result.WIN)


def test_result_messages() -> None:
    game = resolved((("K", "Spades"), ("Q", "Hearts")), (("10", "Clubs"), ("9", "Diamonds")))
    check("win sets a result message", bool(game.result_message))
    check("round is marked over", game.round_over)


# ---------------------------------------------------------------------------
# Flow and state
# ---------------------------------------------------------------------------

def test_initial_deal() -> None:
    game = BlackjackGame()
    game.start_round()
    check("player is dealt 2 cards", len(game.player_hand) == 2)
    check("dealer is dealt 2 cards", len(game.dealer_hand) == 2)
    check("fresh deck leaves 48 cards", len(game.deck) == 48)

    # Roughly 1 in 10 deals is an instant blackjack, which resolves and
    # reveals immediately. Re-deal until a normal round comes up so the
    # mid-round assertion below is actually testing something.
    for _ in range(50):
        if game.state is GameState.PLAYER:
            break
        game.start_round()
    check("dealer hole card starts hidden", not game.dealer_revealed)


def test_dealer_value_hides_hole_card() -> None:
    game = controlled_game((("10", "Spades"), ("9", "Hearts")), (("7", "Clubs"), ("K", "Diamonds")))
    check("hidden dealer shows only the up card", game.dealer_value == 7)

    game.dealer_revealed = True
    check("revealed dealer shows the full total", game.dealer_value == 17)


def test_hit_only_during_player_turn() -> None:
    game = controlled_game((("5", "Spades"), ("6", "Hearts")), (("10", "Clubs"), ("9", "Diamonds")), remaining=(("K", "Spades"),))
    before = len(game.player_hand)
    game.hit()
    check("hit during player turn draws a card", len(game.player_hand) == before + 1)

    game.state = GameState.OVER
    after = len(game.player_hand)
    game.hit()
    check("hit after the round ends is ignored", len(game.player_hand) == after)


def test_hit_bust_ends_round() -> None:
    game = controlled_game((("K", "Spades"), ("9", "Hearts")), (("10", "Clubs"), ("9", "Diamonds")), remaining=(("5", "Spades"),))
    game.hit()
    check("busting on a hit ends the round", game.round_over)
    check("busting player loses", game.result is Result.LOSE)


def test_stand_only_during_player_turn() -> None:
    game = controlled_game((("K", "Spades"), ("9", "Hearts")), (("10", "Clubs"), ("9", "Diamonds")))
    game.state = GameState.OVER
    game.stand()
    check("stand after the round ends is ignored", game.state is GameState.OVER)


def test_new_round_resets_state() -> None:
    game = BlackjackGame()
    game.start_round()
    game.stand()
    check("first round resolved", game.round_over)

    # Deal until the round is not an instant blackjack. Roughly 1 in 10
    # deals resolves on the deal itself (dealer_revealed is then rightly
    # True), which would skip the reset path this test is about.
    for _ in range(50):
        game.start_round()
        if game.state is GameState.PLAYER:
            break

    check("new round starts in the player's turn", game.state is GameState.PLAYER)
    check("new round clears the result", game.result is None)
    check("new round resets the message", game.result_message == "")
    check("new round re-hides the hole card", not game.dealer_revealed)
    check("new round deals 2 cards each", len(game.player_hand) == 2 and len(game.dealer_hand) == 2)


def test_hole_card_hidden_exactly_while_in_play() -> None:
    """
    The hole card is face-down exactly when the player is still acting —
    including on an instant blackjack, where it is revealed immediately.
    """
    for _ in range(200):
        game = BlackjackGame()
        game.start_round()
        in_play = game.state is GameState.PLAYER
        if game.dealer_revealed == in_play:
            check("hole card visibility tracks the game state", False)
            return
    check("hole card visibility tracks the game state", True)


def test_result_enum() -> None:
    check(
        "Result exposes the four outcomes",
        {r.name for r in Result} == {"WIN", "LOSE", "PUSH", "BLACKJACK"},
    )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main() -> int:
    tests = [
        test_deck,
        test_scoring,
        test_score_cards_helper,
        test_soft_flag,
        test_blackjack_detection,
        test_dealer_stands_on_17,
        test_dealer_stands_on_soft_17,
        test_dealer_hits_below_17,
        test_dealer_busts,
        test_resolution,
        test_result_messages,
        test_initial_deal,
        test_dealer_value_hides_hole_card,
        test_hit_only_during_player_turn,
        test_hit_bust_ends_round,
        test_stand_only_during_player_turn,
        test_new_round_resets_state,
        test_hole_card_hidden_exactly_while_in_play,
        test_result_enum,
    ]

    for test in tests:
        test()

    print()
    if _failures:
        print(f"{len(_failures)} of {_checks} checks FAILED:")
        for label in _failures:
            print(f"  - {label}")
        return 1

    print(f"All {_checks} checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
