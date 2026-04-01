from __future__ import annotations


LIGHT_THEME = {
    "background": (0.95, 0.95, 0.95, 1.0),
    "panel": (1.0, 1.0, 1.0, 1.0),
    "panel_soft": (0.98, 0.98, 0.98, 1.0),
    "panel_muted": (0.97, 0.97, 0.97, 1.0),
    "inactive_button": (0.91, 0.91, 0.91, 1.0),
    "inactive_text": (0.25, 0.25, 0.25, 1.0),
    "text": (0.12, 0.12, 0.12, 1.0),
    "subtext": (0.32, 0.32, 0.32, 1.0),
}

DARK_THEME = {
    "background": (0.10, 0.11, 0.12, 1.0),
    "panel": (0.16, 0.17, 0.19, 1.0),
    "panel_soft": (0.19, 0.20, 0.22, 1.0),
    "panel_muted": (0.21, 0.22, 0.24, 1.0),
    "inactive_button": (0.24, 0.25, 0.28, 1.0),
    "inactive_text": (0.92, 0.92, 0.92, 1.0),
    "text": (0.95, 0.95, 0.96, 1.0),
    "subtext": (0.78, 0.78, 0.80, 1.0),
}


def get_theme(dark_mode: bool) -> dict:
    return DARK_THEME if dark_mode else LIGHT_THEME
