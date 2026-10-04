"""
Configuration constants for the Blackjack UI.

All visual parameters — colors, dimensions, positions, fonts —
are defined here so the UI layer stays clean and easily tweakable.
"""

import pygame

# ---------------------------------------------------------------------------
# Window
# ---------------------------------------------------------------------------

WINDOW_WIDTH  = 900
WINDOW_HEIGHT = 650
WINDOW_TITLE  = "Blackjack"
FPS           = 60

# ---------------------------------------------------------------------------
# Colors (RGB)
# ---------------------------------------------------------------------------

COLOR_BG          = (16, 82, 45)      # Dark green felt
COLOR_BG_GRADIENT = (10, 60, 32)      # Slightly darker for depth
COLOR_WHITE       = (255, 255, 255)
COLOR_BLACK       = (0, 0, 0)
COLOR_CARD_BG     = (250, 250, 250)   # Card face
COLOR_CARD_BACK   = (30, 60, 140)     # Card back (blue)
COLOR_CARD_BORDER = (180, 180, 180)
COLOR_RED         = (200, 30, 30)     # Diamonds / Hearts text
COLOR_SUIT_BLACK  = (20, 20, 20)      # Clubs / Spades text

# Button colors
COLOR_BTN_HIT       = (34, 139, 34)   # Green
COLOR_BTN_HIT_HOVER = (50, 170, 50)
COLOR_BTN_STAND     = (178, 34, 34)   # Red
COLOR_BTN_STAND_HOVER = (210, 50, 50)
COLOR_BTN_NEW_GAME  = (30, 100, 200)  # Blue
COLOR_BTN_NEW_GAME_HOVER = (50, 130, 230)
COLOR_BTN_DISABLED  = (100, 100, 100)
COLOR_BTN_TEXT      = (255, 255, 255)
COLOR_BTN_BORDER    = (255, 255, 255)

# Text colors
COLOR_TEXT          = (255, 255, 255)
COLOR_TEXT_SHADOW   = (0, 0, 0)
COLOR_RESULT_WIN    = (80, 220, 80)
COLOR_RESULT_LOSE   = (220, 80, 80)
COLOR_RESULT_PUSH   = (220, 200, 80)
COLOR_RESULT_BJ     = (255, 215, 0)   # Gold

# ---------------------------------------------------------------------------
# Card dimensions
# ---------------------------------------------------------------------------

CARD_WIDTH  = 80
CARD_HEIGHT = 112
CARD_RADIUS = 8            # Rounded corner radius
CARD_SPACING = 20          # Horizontal gap between cards
CARD_OVERLAP = 55          # Overlap when hand has many cards

# ---------------------------------------------------------------------------
# Layout — hand positions (top-left anchor for the first card)
# ---------------------------------------------------------------------------

DEALER_HAND_X = 80
DEALER_HAND_Y = 60

PLAYER_HAND_X = 80
PLAYER_HAND_Y = 380

# Hand value label offsets (relative to hand anchor)
HAND_VALUE_OFFSET_X = 0
HAND_VALUE_OFFSET_Y = -35   # Above the cards

# ---------------------------------------------------------------------------
# Buttons
# ---------------------------------------------------------------------------

BTN_WIDTH  = 140
BTN_HEIGHT = 50
BTN_RADIUS = 10
BTN_SPACING = 30

# Button positions (centered horizontally)
# HIT and STAND appear during player turn
BTN_HIT_X  = WINDOW_WIDTH // 2 - BTN_WIDTH - BTN_SPACING // 2
BTN_HIT_Y  = 560

BTN_STAND_X = WINDOW_WIDTH // 2 + BTN_SPACING // 2
BTN_STAND_Y = 560

# NEW GAME appears after round ends
BTN_NEW_GAME_X = WINDOW_WIDTH // 2 - BTN_WIDTH // 2
BTN_NEW_GAME_Y = 560

# ---------------------------------------------------------------------------
# Result text
# ---------------------------------------------------------------------------

RESULT_TEXT_X = WINDOW_WIDTH // 2
RESULT_TEXT_Y = 300

# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------

pygame.font.init()

FONT_CARD_RANK  = pygame.font.SysFont("segoeuisymbol", 36, bold=True)
FONT_CARD_SUIT  = pygame.font.SysFont("segoeuisymbol", 28)
FONT_HAND_VALUE = pygame.font.SysFont("arial", 22, bold=True)
FONT_BUTTON     = pygame.font.SysFont("arial", 22, bold=True)
FONT_RESULT     = pygame.font.SysFont("arial", 32, bold=True)
FONT_TITLE      = pygame.font.SysFont("arial", 28, bold=True)
