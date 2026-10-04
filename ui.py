"""
Pygame rendering layer for Blackjack.

This file handles all visual output and user input. It imports
game logic from game.py and constants from config.py but contains
no game logic of its own.
"""

import sys
from typing import Callable, List, Sequence, Tuple

import pygame

from game import RED_SUITS, SUIT_SYMBOLS, BlackjackGame, Card, GameState, Result
import config as cfg


# Which color each outcome is drawn in. Presentation lives here, not in
# the engine, so game.py never needs to know about colors.
RESULT_COLORS = {
    Result.WIN:       cfg.COLOR_RESULT_WIN,
    Result.BLACKJACK: cfg.COLOR_RESULT_BJ,
    Result.LOSE:      cfg.COLOR_RESULT_LOSE,
    Result.PUSH:      cfg.COLOR_RESULT_PUSH,
}


# ---------------------------------------------------------------------------
# Button class
# ---------------------------------------------------------------------------

class Button:
    """A clickable button that knows the action it triggers."""

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        color: Tuple[int, int, int],
        hover_color: Tuple[int, int, int],
        font: pygame.font.Font,
        on_click: Callable[[], None],
    ) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.font = font
        self.on_click = on_click
        self.is_hovered = False

    def draw(self, surface: pygame.Surface) -> None:
        """Render the button on the given surface."""
        color = self.hover_color if self.is_hovered else self.color

        # Rounded background, then a border drawn on top of it
        pygame.draw.rect(surface, color, self.rect, border_radius=cfg.BTN_RADIUS)
        pygame.draw.rect(
            surface, cfg.COLOR_BTN_BORDER, self.rect,
            width=cfg.BTN_BORDER_WIDTH, border_radius=cfg.BTN_RADIUS,
        )

        # Centered label
        text_surface = self.font.render(self.text, True, cfg.COLOR_BTN_TEXT)
        surface.blit(text_surface, text_surface.get_rect(center=self.rect.center))

    def update_hover(self, mouse_pos: Tuple[int, int]) -> None:
        """Update hover state based on mouse position."""
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos: Tuple[int, int]) -> bool:
        """Check if the button was clicked at the given position."""
        return self.rect.collidepoint(mouse_pos)


# ---------------------------------------------------------------------------
# Text helper
# ---------------------------------------------------------------------------

def draw_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: Tuple[int, int, int],
    position: Tuple[int, int],
    center: bool = False,
    shadow: bool = False,
) -> None:
    """
    Draw text, optionally centered on `position` and optionally with a
    small drop shadow to keep it legible against the felt.
    """
    rendered = font.render(text, True, color)

    if shadow:
        shadow_surface = font.render(text, True, cfg.COLOR_TEXT_SHADOW)
        shadow_pos = (
            position[0] + cfg.TEXT_SHADOW_OFFSET,
            position[1] + cfg.TEXT_SHADOW_OFFSET,
        )
        if center:
            surface.blit(shadow_surface, shadow_surface.get_rect(center=shadow_pos))
        else:
            surface.blit(shadow_surface, shadow_pos)

    if center:
        surface.blit(rendered, rendered.get_rect(center=position))
    else:
        surface.blit(rendered, position)


# ---------------------------------------------------------------------------
# Card rendering
# ---------------------------------------------------------------------------

def draw_card(
    surface: pygame.Surface,
    x: int,
    y: int,
    card: Card,
    face_up: bool = True,
) -> None:
    """
    Draw a single card at (x, y).

    If face_up is False, draw the card back (dealer's hole card).
    """
    rect = pygame.Rect(x, y, cfg.CARD_WIDTH, cfg.CARD_HEIGHT)

    if not face_up:
        # Card back: solid fill, border, then a lighter inner panel
        pygame.draw.rect(surface, cfg.COLOR_CARD_BACK, rect, border_radius=cfg.CARD_RADIUS)
        pygame.draw.rect(
            surface, cfg.COLOR_CARD_BORDER, rect,
            width=cfg.CARD_BORDER_WIDTH, border_radius=cfg.CARD_RADIUS,
        )
        pygame.draw.rect(
            surface, cfg.COLOR_CARD_BACK_PATTERN,
            rect.inflate(-cfg.CARD_BACK_INSET, -cfg.CARD_BACK_INSET),
            border_radius=cfg.CARD_BACK_PANEL_RADIUS,
        )
        return

    # Card face
    pygame.draw.rect(surface, cfg.COLOR_CARD_BG, rect, border_radius=cfg.CARD_RADIUS)
    pygame.draw.rect(
        surface, cfg.COLOR_CARD_BORDER, rect,
        width=cfg.CARD_BORDER_WIDTH, border_radius=cfg.CARD_RADIUS,
    )

    # Red for hearts and diamonds, black for clubs and spades
    text_color = cfg.COLOR_RED if card.suit in RED_SUITS else cfg.COLOR_SUIT_BLACK
    suit_symbol = SUIT_SYMBOLS[card.suit]

    # Rank in the top-left, with the suit symbol beneath it
    draw_text(surface, card.rank, cfg.FONT_CARD_RANK, text_color,
              (x + cfg.CARD_PADDING, y + cfg.CARD_TOP_PADDING))
    draw_text(surface, suit_symbol, cfg.FONT_CARD_SUIT, text_color,
              (x + cfg.CARD_PADDING, y + cfg.CARD_SUIT_PADDING))

    # Large suit symbol in the middle of the card
    draw_text(surface, suit_symbol, cfg.FONT_CARD_RANK, text_color,
              (x + cfg.CARD_WIDTH // 2,
               y + cfg.CARD_HEIGHT // 2 + cfg.CARD_CENTER_OFFSET),
              center=True)

    # Rank repeated in the bottom-right, rotated 180° so it reads
    # correctly when the card is turned the other way up
    rank_rotated = pygame.transform.rotate(
        cfg.FONT_CARD_RANK.render(card.rank, True, text_color), 180
    )
    surface.blit(rank_rotated, (
        x + cfg.CARD_WIDTH - rank_rotated.get_width() - cfg.CARD_PADDING,
        y + cfg.CARD_HEIGHT - rank_rotated.get_height() - cfg.CARD_TOP_PADDING,
    ))


def hand_spacing(card_count: int) -> int:
    """
    Horizontal gap between cards in a hand.

    Cards sit at the normal spacing unless that would overflow the
    table, in which case they compress down to the tightest allowed gap.
    """
    if card_count < 2:
        return cfg.CARD_SPACING

    natural_width = card_count * cfg.CARD_WIDTH + (card_count - 1) * cfg.CARD_SPACING
    if natural_width <= cfg.CARD_MAX_HAND_WIDTH:
        return cfg.CARD_SPACING

    compressed = (cfg.CARD_MAX_HAND_WIDTH - card_count * cfg.CARD_WIDTH) // (card_count - 1)
    return max(compressed, cfg.CARD_MIN_SPACING)


def draw_hand(
    surface: pygame.Surface,
    cards: Sequence[Card],
    start_x: int,
    start_y: int,
    face_down: Sequence[int] = (),
) -> None:
    """
    Draw a hand of cards starting at (start_x, start_y).

    `face_down` lists the indices to draw face-down — the dealer's hole
    card, which is always index 1 while the round is still in play.
    """
    spacing = hand_spacing(len(cards))
    for index, card in enumerate(cards):
        draw_card(
            surface,
            start_x + index * (cfg.CARD_WIDTH + spacing),
            start_y,
            card,
            face_up=index not in face_down,
        )


# ---------------------------------------------------------------------------
# Main UI class
# ---------------------------------------------------------------------------

class BlackjackUI:
    """Pygame-based UI for the Blackjack game."""

    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode(
            (cfg.WINDOW_WIDTH, cfg.WINDOW_HEIGHT)
        )
        pygame.display.set_caption(cfg.WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.game = BlackjackGame()

        # Each button carries the action it performs, so click dispatch
        # needs no mapping table: adding a button means creating it here
        # and listing it in active_buttons().
        self.btn_hit = Button(
            cfg.BTN_HIT_X, cfg.BTN_HIT_Y,
            cfg.BTN_WIDTH, cfg.BTN_HEIGHT,
            "HIT",
            cfg.COLOR_BTN_HIT, cfg.COLOR_BTN_HIT_HOVER,
            cfg.FONT_BUTTON,
            on_click=self.game.hit,
        )
        self.btn_stand = Button(
            cfg.BTN_STAND_X, cfg.BTN_STAND_Y,
            cfg.BTN_WIDTH, cfg.BTN_HEIGHT,
            "STAND",
            cfg.COLOR_BTN_STAND, cfg.COLOR_BTN_STAND_HOVER,
            cfg.FONT_BUTTON,
            on_click=self.game.stand,
        )
        self.btn_new_game = Button(
            cfg.BTN_NEW_GAME_X, cfg.BTN_NEW_GAME_Y,
            cfg.BTN_WIDTH, cfg.BTN_HEIGHT,
            "NEW GAME",
            cfg.COLOR_BTN_NEW_GAME, cfg.COLOR_BTN_NEW_GAME_HOVER,
            cfg.FONT_BUTTON,
            on_click=self.game.start_round,
        )

        # Deal the first round straight away
        self.game.start_round()

    # ------------------------------------------------------------------
    # Button visibility
    # ------------------------------------------------------------------

    def active_buttons(self) -> List[Button]:
        """
        The buttons that are clickable in the current game state.

        Single source of truth: drawing and click handling both read
        this, so they can never disagree about what is on screen.
        """
        if self.game.state == GameState.PLAYER:
            return [self.btn_hit, self.btn_stand]
        if self.game.round_over:
            return [self.btn_new_game]
        return []

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw_background(self) -> None:
        """Fill the background with a solid dark green."""
        self.screen.fill(cfg.COLOR_BG)

    def draw_hand_value(self, x: int, y: int, label: str, value: int) -> None:
        """Draw a hand value label (e.g. 'Dealer: 17')."""
        draw_text(self.screen, f"{label}: {value}", cfg.FONT_HAND_VALUE,
                  cfg.COLOR_TEXT, (x, y), shadow=True)

    def draw_result(self) -> None:
        """Draw the round result text at the center of the screen."""
        if not self.game.round_over or not self.game.result_message:
            return

        color = RESULT_COLORS.get(self.game.result, cfg.COLOR_RESULT_PUSH)
        draw_text(self.screen, self.game.result_message, cfg.FONT_RESULT, color,
                  (cfg.RESULT_TEXT_X, cfg.RESULT_TEXT_Y), center=True, shadow=True)

    def draw(self) -> None:
        """Render the entire frame."""
        self.draw_background()

        # Dealer hand, with the hole card face-down until it is revealed
        face_down = () if self.game.dealer_revealed else (1,)
        draw_hand(
            self.screen,
            self.game.dealer_hand.cards,
            cfg.DEALER_HAND_X,
            cfg.DEALER_HAND_Y,
            face_down=face_down,
        )
        self.draw_hand_value(
            cfg.DEALER_HAND_X + cfg.HAND_VALUE_OFFSET_X,
            cfg.DEALER_HAND_Y + cfg.HAND_VALUE_OFFSET_Y,
            "Dealer",
            self.game.dealer_value,
        )

        # Player hand
        draw_hand(
            self.screen,
            self.game.player_hand.cards,
            cfg.PLAYER_HAND_X,
            cfg.PLAYER_HAND_Y,
        )
        self.draw_hand_value(
            cfg.PLAYER_HAND_X + cfg.HAND_VALUE_OFFSET_X,
            cfg.PLAYER_HAND_Y + cfg.HAND_VALUE_OFFSET_Y,
            "Player",
            self.game.player_value,
        )

        self.draw_result()

        # Hover is refreshed from the live mouse position every frame,
        # so no MOUSEMOTION handling is needed.
        mouse_pos = pygame.mouse.get_pos()
        for button in self.active_buttons():
            button.update_hover(mouse_pos)
            button.draw(self.screen)

        pygame.display.flip()

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def handle_events(self) -> bool:
        """
        Process Pygame events. Returns False if the game should quit.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in self.active_buttons():
                    if button.is_clicked(event.pos):
                        button.on_click()
                        break

        return True

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Main game loop."""
        running = True
        while running:
            running = self.handle_events()
            self.draw()
            self.clock.tick(cfg.FPS)

        pygame.quit()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    BlackjackUI().run()
    sys.exit(0)
