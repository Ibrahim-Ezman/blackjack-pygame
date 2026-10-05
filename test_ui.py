"""
Headless smoke test for the UI layer.

Drives the real BlackjackUI with synthetic pygame events under a dummy
video driver, so button dispatch, hover, drawing and the main loop are
all exercised without opening a window.

    python test_ui.py
"""

import os
import threading
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402  (must follow the SDL driver setting)

from game import GameState, Result  # noqa: E402
from ui import BlackjackUI, hand_spacing  # noqa: E402
import config as cfg  # noqa: E402

_failures: list[str] = []
_checks = 0


def check(label: str, condition: bool) -> None:
    global _checks
    _checks += 1
    if condition:
        print(f"PASS: {label}")
    else:
        print(f"FAIL: {label}")
        _failures.append(label)


def click(ui: BlackjackUI, button) -> None:
    """Post a synthetic left-click on the given button and process it."""
    pygame.event.post(
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": button.rect.center, "button": 1})
    )
    ui.handle_events()


def test_button_visibility() -> None:
    ui = BlackjackUI()
    ui.game.state = GameState.PLAYER
    check("player turn shows HIT and STAND",
          ui.active_buttons() == [ui.btn_hit, ui.btn_stand])

    ui.game.state = GameState.OVER
    check("round over shows only NEW GAME",
          ui.active_buttons() == [ui.btn_new_game])

    ui.game.state = GameState.DEALER
    check("dealer turn shows no buttons", ui.active_buttons() == [])


def test_hit_button_dispatch() -> None:
    ui = BlackjackUI()
    ui.game.state = GameState.PLAYER
    before = len(ui.game.player_hand)
    click(ui, ui.btn_hit)
    check("clicking HIT draws a card", len(ui.game.player_hand) == before + 1)


def test_stand_button_dispatch() -> None:
    ui = BlackjackUI()
    ui.game.state = GameState.PLAYER
    click(ui, ui.btn_stand)
    check("clicking STAND ends the round", ui.game.round_over)
    check("standing yields a real result", ui.game.result in tuple(Result))


def test_new_game_button_dispatch() -> None:
    ui = BlackjackUI()
    ui.game.state = GameState.PLAYER
    click(ui, ui.btn_stand)
    check("round is over before restart", ui.game.round_over)

    # NEW GAME can itself deal an instant blackjack (~1 in 10), in which
    # case the hole card is correctly already revealed. Retry until a
    # normal round comes up, then assert on that one.
    for _ in range(50):
        click(ui, ui.btn_new_game)
        if ui.game.state is GameState.PLAYER:
            break

    check("NEW GAME deals a fresh hand", len(ui.game.player_hand) == 2)
    check("NEW GAME starts a playable round", ui.game.state is GameState.PLAYER)
    check("NEW GAME hides the hole card again", not ui.game.dealer_revealed)


def test_click_on_empty_space_is_ignored() -> None:
    ui = BlackjackUI()
    ui.game.state = GameState.PLAYER
    before = len(ui.game.player_hand)
    pygame.event.post(
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (5, 5), "button": 1})
    )
    ui.handle_events()
    check("clicking the felt does nothing", len(ui.game.player_hand) == before)


def test_hover_tracking() -> None:
    ui = BlackjackUI()
    ui.game.state = GameState.PLAYER
    ui.btn_hit.update_hover(ui.btn_hit.rect.center)
    check("hovering a button sets its hover flag", ui.btn_hit.is_hovered)
    ui.btn_hit.update_hover((5, 5))
    check("moving off a button clears its hover flag", not ui.btn_hit.is_hovered)


def test_draw_does_not_crash() -> None:
    """Every visual state must render without raising."""
    ui = BlackjackUI()

    # Mid-round: hole card hidden, HIT/STAND visible
    ui.game.state = GameState.PLAYER
    ui.draw()

    # Dealer's turn: no buttons at all
    ui.game.state = GameState.DEALER
    ui.draw()

    # Round over: result text plus NEW GAME
    ui.game.state = GameState.PLAYER
    ui.game.stand()
    ui.draw()
    check("all three visual states render", ui.game.round_over)

    # A long hand exercises the compressed card spacing
    ui.game.state = GameState.PLAYER
    for _ in range(8):
        ui.game.hit()
        ui.draw()
    check("long hands render (compressed spacing)", len(ui.game.player_hand) >= 2)


def test_hand_spacing_compresses() -> None:
    check("two cards use normal spacing", hand_spacing(2) == cfg.CARD_SPACING)
    check("a long hand compresses", hand_spacing(10) < cfg.CARD_SPACING)
    check("compressed spacing never goes below the minimum",
          hand_spacing(10) >= cfg.CARD_MIN_SPACING)


def test_quit_event() -> None:
    ui = BlackjackUI()
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    check("QUIT event stops the loop", ui.handle_events() is False)


def test_run_loop_exits_on_quit() -> None:
    """
    Drive the real run() loop, not just its pieces.

    Posts a QUIT from a timer thread, so if the loop ever stops noticing
    QUIT events the test hangs and CI times out instead of silently
    passing. run() returns on its own once the loop exits.
    """
    ui = BlackjackUI()

    def quit_soon() -> None:
        time.sleep(0.3)
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    threading.Thread(target=quit_soon, daemon=True).start()
    ui.run()
    check("run() returns after a QUIT event", True)


def test_full_round_end_to_end() -> None:
    """Play a whole round through the UI until the engine reports a result."""
    ui = BlackjackUI()
    guard = 0
    while not ui.game.round_over and guard < 30:
        click(ui, ui.btn_stand)
        guard += 1
    check("a round can be played to completion via buttons", ui.game.round_over)
    check("the finished round has a message", bool(ui.game.result_message))

    # NEW GAME may deal an instant blackjack, which is over the moment it
    # is dealt. Keep restarting until a normal round comes up.
    for _ in range(50):
        if not ui.game.round_over:
            break
        click(ui, ui.btn_new_game)
    check("a new round starts cleanly afterwards", not ui.game.round_over)


def main() -> int:
    tests = [
        test_button_visibility,
        test_hit_button_dispatch,
        test_stand_button_dispatch,
        test_new_game_button_dispatch,
        test_click_on_empty_space_is_ignored,
        test_hover_tracking,
        test_draw_does_not_crash,
        test_hand_spacing_compresses,
        test_quit_event,
        test_run_loop_exits_on_quit,
        test_full_round_end_to_end,
    ]

    for test in tests:
        test()

    pygame.quit()

    print()
    if _failures:
        print(f"{len(_failures)} of {_checks} checks FAILED:")
        for label in _failures:
            print(f"  - {label}")
        return 1

    print(f"All {_checks} UI checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
