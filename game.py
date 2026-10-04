"""
Blackjack game logic — no rendering, no I/O.

This module contains the complete game engine: deck management,
hand scoring with soft-ace correction, dealer AI, and game state
tracking. It is fully independent of Pygame and can be tested
in isolation.
"""

import random
from enum import Enum
from dataclasses import dataclass
from typing import List


# ---------------------------------------------------------------------------
# Card representation
# ---------------------------------------------------------------------------

SUITS = ("Hearts", "Diamonds", "Clubs", "Spades")
RANKS = ("2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A")

# Display symbols for suits (Unicode, rendered by the UI layer)
SUIT_SYMBOLS = {
    "Hearts":   "♥",
    "Diamonds": "♦",
    "Clubs":    "♣",
    "Spades":   "♠",
}

# Base value for each rank before soft-ace correction
RANK_VALUES = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7,
    "8": 8, "9": 9, "10": 10, "J": 10, "Q": 10, "K": 10, "A": 11,
}


@dataclass(frozen=True)
class Card:
    """A single playing card."""
    rank: str
    suit: str

    @property
    def value(self) -> int:
        """Base value of the card (Ace = 11 before correction)."""
        return RANK_VALUES[self.rank]

    def __str__(self) -> str:
        return f"{self.rank}{SUIT_SYMBOLS[self.suit]}"


# ---------------------------------------------------------------------------
# Game states
# ---------------------------------------------------------------------------

class GameState(Enum):
    """Finite-state machine for the game lifecycle."""
    DEALING   = "dealing"    # Initial deal in progress
    PLAYER    = "player"     # Player's turn (hit or stand)
    DEALER    = "dealer"     # Dealer's turn (auto-play)
    OVER      = "over"       # Round finished, show result


# ---------------------------------------------------------------------------
# Hand
# ---------------------------------------------------------------------------

class Hand:
    """A collection of cards with scoring logic."""

    def __init__(self) -> None:
        self.cards: List[Card] = []

    def add(self, card: Card) -> None:
        self.cards.append(card)

    def clear(self) -> None:
        self.cards.clear()

    @property
    def value(self) -> int:
        """
        Best hand value ≤ 21, or the minimum possible value if bust.

        Algorithm: sum all cards with Ace = 11, then demote Aces
        to 1 (subtract 10 each) while the total exceeds 21.
        """
        total = sum(c.value for c in self.cards)
        aces = sum(1 for c in self.cards if c.rank == "A")
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return total

    @property
    def is_bust(self) -> bool:
        return self.value > 21

    @property
    def is_blackjack(self) -> bool:
        """True if the hand is exactly 21 with two cards."""
        return len(self.cards) == 2 and self.value == 21

    @property
    def is_soft(self) -> bool:
        """
        A hand is 'soft' if it contains an Ace counted as 11
        (i.e. demoting it would lower the total).
        """
        total = sum(c.value for c in self.cards)
        aces = sum(1 for c in self.cards if c.rank == "A")
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
        return aces > 0  # at least one Ace still counted as 11

    def __len__(self) -> int:
        return len(self.cards)

    def __str__(self) -> str:
        return ", ".join(str(c) for c in self.cards)


# ---------------------------------------------------------------------------
# Deck
# ---------------------------------------------------------------------------

class Deck:
    """A standard 52-card deck, shuffled on creation."""

    def __init__(self) -> None:
        self.cards: List[Card] = [
            Card(rank, suit) for suit in SUITS for rank in RANKS
        ]
        random.shuffle(self.cards)

    def deal(self) -> Card:
        """Remove and return the top card."""
        if not self.cards:
            raise IndexError("Deck is empty")
        return self.cards.pop()

    def __len__(self) -> int:
        return len(self.cards)


# ---------------------------------------------------------------------------
# Game engine
# ---------------------------------------------------------------------------

class BlackjackGame:
    """
    Complete game engine for a single round of Blackjack.

    Usage:
        game = BlackjackGame()
        game.start_round()
        game.hit()
        game.stand()
        game.start_round()   # play again
    """

    def __init__(self) -> None:
        self.deck = Deck()
        self.player_hand = Hand()
        self.dealer_hand = Hand()
        self.state = GameState.DEALING
        self.result: str = ""          # "win", "lose", "push", "blackjack"
        self.result_message: str = ""  # Human-readable result text
        self.dealer_revealed = False   # Whether dealer's hole card is visible

    # ------------------------------------------------------------------
    # Round lifecycle
    # ------------------------------------------------------------------

    def start_round(self) -> None:
        """Reset hands and deal initial cards."""
        self.player_hand.clear()
        self.dealer_hand.clear()
        self.deck = Deck()
        self.result = ""
        self.result_message = ""
        self.dealer_revealed = False
        self.state = GameState.DEALING

        # Deal alternating: player, dealer, player, dealer
        self.player_hand.add(self.deck.deal())
        self.dealer_hand.add(self.deck.deal())
        self.player_hand.add(self.deck.deal())
        self.dealer_hand.add(self.deck.deal())

        # Check for instant blackjack on either side
        if self.player_hand.is_blackjack or self.dealer_hand.is_blackjack:
            self._finish_round()
        else:
            self.state = GameState.PLAYER

    # ------------------------------------------------------------------
    # Player actions
    # ------------------------------------------------------------------

    def hit(self) -> None:
        """Player draws one card. Bust ends the round."""
        if self.state != GameState.PLAYER:
            return
        self.player_hand.add(self.deck.deal())
        if self.player_hand.is_bust:
            self._finish_round()

    def stand(self) -> None:
        """Player ends their turn; dealer plays automatically."""
        if self.state != GameState.PLAYER:
            return
        self.state = GameState.DEALER
        self._dealer_play()

    # ------------------------------------------------------------------
    # Dealer AI
    # ------------------------------------------------------------------

    def _dealer_play(self) -> None:
        """
        Dealer reveals hole card, then hits until hand value ≥ 17.
        Standard casino rule: dealer stands on soft 17.
        """
        self.dealer_revealed = True
        while self.dealer_hand.value < 17:
            self.dealer_hand.add(self.deck.deal())
        self._finish_round()

    # ------------------------------------------------------------------
    # Round resolution
    # ------------------------------------------------------------------

    def _finish_round(self) -> None:
        """Compare hands and set the result."""
        self.dealer_revealed = True
        self.state = GameState.OVER

        pv = self.player_hand.value
        dv = self.dealer_hand.value
        p_bust = self.player_hand.is_bust
        d_bust = self.dealer_hand.is_bust
        p_bj = self.player_hand.is_blackjack
        d_bj = self.dealer_hand.is_blackjack

        # Both blackjack = push
        if p_bj and d_bj:
            self.result = "push"
            self.result_message = "Push — both have Blackjack!"
        # Player blackjack wins (unless dealer also has it, handled above)
        elif p_bj:
            self.result = "blackjack"
            self.result_message = "Blackjack! You win!"
        # Dealer blackjack wins
        elif d_bj:
            self.result = "lose"
            self.result_message = "Dealer has Blackjack. You lose."
        # Player bust = immediate loss
        elif p_bust:
            self.result = "lose"
            self.result_message = f"Bust! You went over 21 ({pv})."
        # Dealer bust = player wins
        elif d_bust:
            self.result = "win"
            self.result_message = f"Dealer busts with {dv}. You win!"
        # Compare values
        elif pv > dv:
            self.result = "win"
            self.result_message = f"You win! {pv} vs {dv}."
        elif dv > pv:
            self.result = "lose"
            self.result_message = f"Dealer wins. {dv} vs {pv}."
        else:
            self.result = "push"
            self.result_message = f"Push — both have {pv}."

    # ------------------------------------------------------------------
    # Convenience properties for the UI
    # ------------------------------------------------------------------

    @property
    def player_value(self) -> int:
        return self.player_hand.value

    @property
    def dealer_value(self) -> int:
        """Dealer value — only counts revealed cards during play."""
        if self.dealer_revealed:
            return self.dealer_hand.value
        # Hide hole card: only count the first (face-up) card
        if self.dealer_hand.cards:
            first = self.dealer_hand.cards[0]
            return RANK_VALUES[first.rank]
        return 0

    @property
    def round_over(self) -> bool:
        return self.state == GameState.OVER
