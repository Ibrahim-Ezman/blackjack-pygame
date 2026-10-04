"""
Regenerate the screenshots in this folder.

Renders the game headlessly (SDL's dummy video driver) with fixed hands,
so the images are reproducible rather than hand-captured.

    python docs/make_screenshots.py

Can be run from anywhere. The screenshots are produced by the real
renderer in ui.py — nothing is mocked or drawn separately for the README.
"""

import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"

# Running this file puts docs/ on sys.path, not the repository root, so
# add the root explicitly before importing the game modules.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import pygame  # noqa: E402

import ui  # noqa: E402
from game import Card, GameState  # noqa: E402

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def save(app: ui.BlackjackUI, filename: str) -> None:
    path = os.path.join(OUTPUT_DIR, filename)
    app.draw()
    pygame.image.save(app.screen, path)
    print(f"wrote {path}")


def set_hands(app: ui.BlackjackUI, player: list, dealer: list) -> None:
    """Replace both hands with fixed cards, for a stable screenshot."""
    app.game.player_hand.clear()
    for rank, suit in player:
        app.game.player_hand.add(Card(rank, suit))
    app.game.dealer_hand.clear()
    for rank, suit in dealer:
        app.game.dealer_hand.add(Card(rank, suit))


def main() -> None:
    app = ui.BlackjackUI()

    # Mid-round: the hole card is face down and HIT/STAND are showing.
    set_hands(
        app,
        player=[("A", "Spades"), ("K", "Hearts")],
        dealer=[("10", "Diamonds"), ("7", "Clubs")],
    )
    app.game.dealer_revealed = False
    app.game.state = GameState.PLAYER
    app.game.result = ""
    app.game.result_message = ""
    save(app, "gameplay.png")

    # Finished round: player blackjack, resolved by the real engine.
    set_hands(
        app,
        player=[("A", "Spades"), ("K", "Hearts")],
        dealer=[("10", "Diamonds"), ("9", "Clubs")],
    )
    app.game._finish_round()
    save(app, "result-blackjack.png")

    pygame.quit()


if __name__ == "__main__":
    main()
