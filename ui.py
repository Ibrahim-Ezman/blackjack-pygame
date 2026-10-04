"""
Pygame rendering layer for Blackjack.

This file handles all visual output and user input. It imports
game logic from game.py and constants from config.py but contains
no game logic of its own.
"""

import pygame
import sys
from typing import Optional, Tuple

from game import BlackjackGame, GameState, Card, SUIT_SYMBOLS
import config as cfg


# ---------------------------------------------------------------------------
# Button class
# ---------------------------------------------------------------------------

class Button:
    """A clickable button with hover effect."""

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
    ) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.font = font
        self.is_hovered = False

    def draw(self, surface: pygame.Surface) -> None:
        """Render the button on the given surface."""
        color = self.hover_color if self.is_hovered else self.color

        # Draw rounded rectangle background
        pygame.draw.rect(surface, color, self.rect, border_radius=cfg.BTN_RADIUS)

        # Draw border
        pygame.draw.rect(
            surface, cfg.COLOR_BTN_BORDER, self.rect,
            width=2, border_radius=cfg.BTN_RADIUS,
        )

        # Draw centered text
        text_surface = self.font.render(self.text, True, cfg.COLOR_BTN_TEXT)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def update_hover(self, mouse_pos: Tuple[int, int]) -> None:
        """Update hover state based on mouse position."""
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos: Tuple[int, int]) -> bool:
        """Check if the button was clicked at the given position."""
        return self.rect.collidepoint(mouse_pos)


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
        # Card back — solid color with a subtle pattern
        pygame.draw.rect(
            surface, cfg.COLOR_CARD_BACK, rect,
            border_radius=cfg.CARD_RADIUS,
        )
        pygame.draw.rect(
            surface, cfg.COLOR_CARD_BORDER, rect,
            width=2, border_radius=cfg.CARD_RADIUS,
        )
        # Simple cross-hatch pattern on the back
        inner = rect.inflate(-12, -12)
        pygame.draw.rect(
            surface, (50, 80, 180), inner,
            border_radius=cfg.CARD_RADIUS - 4,
        )
        return

    # Card face
    pygame.draw.rect(
        surface, cfg.COLOR_CARD_BG, rect,
        border_radius=cfg.CARD_RADIUS,
    )
    pygame.draw.rect(
        surface, cfg.COLOR_CARD_BORDER, rect,
        width=2, border_radius=cfg.CARD_RADIUS,
    )

    # Determine text color based on suit
    is_red = card.suit in ("Hearts", "Diamonds")
    text_color = cfg.COLOR_RED if is_red else cfg.COLOR_SUIT_BLACK

    # Draw rank in top-left
    rank_surface = cfg.FONT_CARD_RANK.render(card.rank, True, text_color)
    surface.blit(rank_surface, (x + 6, y + 4))

    # Draw suit symbol below rank
    suit_symbol = SUIT_SYMBOLS[card.suit]
    suit_surface = cfg.FONT_CARD_SUIT.render(suit_symbol, True, text_color)
    surface.blit(suit_surface, (x + 6, y + 42))

    # Draw large suit symbol in center
    center_suit = cfg.FONT_CARD_RANK.render(suit_symbol, True, text_color)
    center_rect = center_suit.get_rect(
        center=(x + cfg.CARD_WIDTH // 2, y + cfg.CARD_HEIGHT // 2 + 10)
    )
    surface.blit(center_suit, center_rect)

    # Draw rank in bottom-right (rotated 180°)
    rank_br = cfg.FONT_CARD_RANK.render(card.rank, True, text_color)
    rank_br = pygame.transform.rotate(rank_br, 180)
    surface.blit(rank_br, (x + cfg.CARD_WIDTH - rank_br.get_width() - 6,
                           y + cfg.CARD_HEIGHT - rank_br.get_height() - 4))


def draw_hand(
    surface: pygame.Surface,
    cards: list,
    start_x: int,
    start_y: int,
    hide_second: bool = False,
) -> None:
    """
    Draw a hand of cards starting at (start_x, start_y).

    If hide_second is True, the second card is drawn face-down
    (used for the dealer's hole card).
    """
    # Use overlap if many cards to keep the hand on screen
    total_width = len(cards) * cfg.CARD_WIDTH + (len(cards) - 1) * cfg.CARD_SPACING
    available = cfg.WINDOW_WIDTH - 160  # margins on both sides
    if total_width > available and len(cards) > 1:
        spacing = (available - len(cards) * cfg.CARD_WIDTH) // (len(cards) - 1)
        spacing = max(spacing, 10)
    else:
        spacing = cfg.CARD_SPACING

    for i, card in enumerate(cards):
        x = start_x + i * (cfg.CARD_WIDTH + spacing)
        face_up = not (hide_second and i == 1)
        draw_card(surface, x, start_y, card, face_up=face_up)


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

        # Create buttons
        self.btn_hit = Button(
            cfg.BTN_HIT_X, cfg.BTN_HIT_Y,
            cfg.BTN_WIDTH, cfg.BTN_HEIGHT,
            "HIT",
            cfg.COLOR_BTN_HIT, cfg.COLOR_BTN_HIT_HOVER,
            cfg.FONT_BUTTON,
        )
        self.btn_stand = Button(
            cfg.BTN_STAND_X, cfg.BTN_STAND_Y,
            cfg.BTN_WIDTH, cfg.BTN_HEIGHT,
            "STAND",
            cfg.COLOR_BTN_STAND, cfg.COLOR_BTN_STAND_HOVER,
            cfg.FONT_BUTTON,
        )
        self.btn_new_game = Button(
            cfg.BTN_NEW_GAME_X, cfg.BTN_NEW_GAME_Y,
            cfg.BTN_WIDTH, cfg.BTN_HEIGHT,
            "NEW GAME",
            cfg.COLOR_BTN_NEW_GAME, cfg.COLOR_BTN_NEW_GAME_HOVER,
            cfg.FONT_BUTTON,
        )

        # Start the first round
        self.game.start_round()

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw_background(self) -> None:
        """Fill the background with a solid dark green."""
        self.screen.fill(cfg.COLOR_BG)

    def draw_hand_value(
        self,
        x: int,
        y: int,
        label: str,
        value: int,
    ) -> None:
        """Draw a hand value label (e.g. 'Dealer: 17')."""
        text = f"{label}: {value}"
        # Shadow
        shadow = cfg.FONT_HAND_VALUE.render(text, True, cfg.COLOR_TEXT_SHADOW)
        self.screen.blit(shadow, (x + 1, y + 1))
        # Main text
        surface = cfg.FONT_HAND_VALUE.render(text, True, cfg.COLOR_TEXT)
        self.screen.blit(surface, (x, y))

    def draw_result(self) -> None:
        """Draw the round result text at the center of the screen."""
        if not self.game.round_over or not self.game.result_message:
            return

        # Choose color based on result
        result = self.game.result
        if result == "win":
            color = cfg.COLOR_RESULT_WIN
        elif result == "blackjack":
            color = cfg.COLOR_RESULT_BJ
        elif result == "lose":
            color = cfg.COLOR_RESULT_LOSE
        else:
            color = cfg.COLOR_RESULT_PUSH

        # Shadow
        shadow = cfg.FONT_RESULT.render(
            self.game.result_message, True, cfg.COLOR_TEXT_SHADOW
        )
        shadow_rect = shadow.get_rect(
            center=(cfg.RESULT_TEXT_X + 2, cfg.RESULT_TEXT_Y + 2)
        )
        self.screen.blit(shadow, shadow_rect)

        # Main text
        text_surface = cfg.FONT_RESULT.render(
            self.game.result_message, True, color
        )
        text_rect = text_surface.get_rect(
            center=(cfg.RESULT_TEXT_X, cfg.RESULT_TEXT_Y)
        )
        self.screen.blit(text_surface, text_rect)

    def draw(self) -> None:
        """Render the entire frame."""
        self.draw_background()

        # Draw dealer hand
        hide_hole = not self.game.dealer_revealed
        draw_hand(
            self.screen,
            self.game.dealer_hand.cards,
            cfg.DEALER_HAND_X,
            cfg.DEALER_HAND_Y,
            hide_second=hide_hole,
        )

        # Draw dealer value label
        self.draw_hand_value(
            cfg.DEALER_HAND_X + cfg.HAND_VALUE_OFFSET_X,
            cfg.DEALER_HAND_Y + cfg.HAND_VALUE_OFFSET_Y,
            "Dealer",
            self.game.dealer_value,
        )

        # Draw player hand
        draw_hand(
            self.screen,
            self.game.player_hand.cards,
            cfg.PLAYER_HAND_X,
            cfg.PLAYER_HAND_Y,
        )

        # Draw player value label
        self.draw_hand_value(
            cfg.PLAYER_HAND_X + cfg.HAND_VALUE_OFFSET_X,
            cfg.PLAYER_HAND_Y + cfg.HAND_VALUE_OFFSET_Y,
            "Player",
            self.game.player_value,
        )

        # Draw result text
        self.draw_result()

        # Draw buttons based on game state
        mouse_pos = pygame.mouse.get_pos()

        if self.game.state == GameState.PLAYER:
            self.btn_hit.update_hover(mouse_pos)
            self.btn_stand.update_hover(mouse_pos)
            self.btn_hit.draw(self.screen)
            self.btn_stand.draw(self.screen)
        elif self.game.round_over:
            self.btn_new_game.update_hover(mouse_pos)
            self.btn_new_game.draw(self.screen)

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
                mouse_pos = event.pos

                if self.game.state == GameState.PLAYER:
                    if self.btn_hit.is_clicked(mouse_pos):
                        self.game.hit()
                    elif self.btn_stand.is_clicked(mouse_pos):
                        self.game.stand()

                elif self.game.round_over:
                    if self.btn_new_game.is_clicked(mouse_pos):
                        self.game.start_round()

            # Also handle mouse motion for hover updates
            if event.type == pygame.MOUSEMOTION:
                mouse_pos = event.pos
                if self.game.state == GameState.PLAYER:
                    self.btn_hit.update_hover(mouse_pos)
                    self.btn_stand.update_hover(mouse_pos)
                elif self.game.round_over:
                    self.btn_new_game.update_hover(mouse_pos)

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
        sys.exit()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    ui = BlackjackUI()
    ui.run()
