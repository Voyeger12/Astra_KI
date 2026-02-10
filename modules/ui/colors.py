"""
ASTRA UI - Farben und Design-Konstanten
========================================
Zentrale Verwaltung aller Farben und Design-Einstellungen
"""

# Globale Farbpalette (aus config.py importiert)
from config import COLORS

# Zusätzliche UI-Konstanten
UI_CONSTANTS = {
    'WINDOW_WIDTH': 1200,
    'WINDOW_HEIGHT': 800,
    'CHAT_BUBBLE_BORDER_RADIUS': 20,
    'BUTTON_BORDER_RADIUS': 12,
    'INPUT_BORDER_RADIUS': 10,
    'CHECKBOX_SIZE': 20,
    'CHECKBOX_BORDER_RADIUS': 4,
    'MIN_CHECKBOX_HEIGHT': 28,
    'BUBBLE_SHADOW_BLUR': 10,
    'BUBBLE_SHADOW_OFFSET': 2,
    'BUBBLE_PADDING': 12,
    'FONT_SIZE_CHAT': 10,
    'FONT_SIZE_BUTTON': 10,
    'DEFAULT_TEXT_SIZE': 11,
    'MIN_TEXT_SIZE': 9,
    'MAX_TEXT_SIZE': 16,
}

__all__ = ['COLORS', 'UI_CONSTANTS']
