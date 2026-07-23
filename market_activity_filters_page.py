"""Render the Market Activity Filters HTML widget page."""

from __future__ import annotations

from pathlib import Path

_TEMPLATE_PATH = Path(__file__).with_name("templates") / "market_activity_filters.html"


def render_market_activity_filters_page(
    *,
    theme: str,
    controls_json: str,
    initial_state_json: str,
) -> str:
    template = _TEMPLATE_PATH.read_text(encoding="utf-8")
    return (
        template.replace("__THEME__", theme)
        .replace("__CONTROLS_JSON__", controls_json)
        .replace("__INITIAL_STATE_JSON__", initial_state_json)
    )
