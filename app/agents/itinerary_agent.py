"""Itinerary agent: structures raw activities into morning/afternoon/evening slots."""
from __future__ import annotations

import logging
from typing import Any

from app.schemas.models import AgentState

logger = logging.getLogger(__name__)

_MORNING_SLOTS = ["6:00 AM", "7:00 AM", "8:00 AM", "9:00 AM", "10:00 AM", "11:00 AM"]
_AFTERNOON_SLOTS = ["12:00 PM", "1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM"]
_EVENING_SLOTS = ["6:00 PM", "7:00 PM", "8:00 PM", "9:00 PM", "10:00 PM"]


def _slot_to_period(time_slot: str) -> str:
    """Determine morning/afternoon/evening from the time slot string."""
    slot_upper = time_slot.upper()
    # Check for AM/PM markers (use full slot string to avoid AM/PM collisions)
    for s in _MORNING_SLOTS:
        if s in slot_upper or slot_upper.startswith(s):
            return "morning"
    for s in _AFTERNOON_SLOTS:
        if s in slot_upper or slot_upper.startswith(s):
            return "afternoon"
    for s in _EVENING_SLOTS:
        if s in slot_upper or slot_upper.startswith(s):
            return "evening"
    # Fallback: parse hour
    try:
        hour_part = time_slot.split(":")[0].strip()
        hour = int(hour_part)
        if 5 <= hour < 12:
            return "morning"
        if 12 <= hour < 17:
            return "afternoon"
        return "evening"
    except (ValueError, IndexError):
        return "afternoon"


async def itinerary_node(state: AgentState) -> AgentState:
    """Organise raw activities into a structured day plan."""
    activities: list[dict[str, Any]] = state.get("raw_activities", [])
    weather_category = state.get("weather_category", "pleasant")

    morning: list[dict] = []
    afternoon: list[dict] = []
    evening: list[dict] = []

    for activity in activities:
        period = _slot_to_period(activity.get("time_slot", "12:00 PM"))
        if period == "morning":
            morning.append(activity)
        elif period == "afternoon":
            afternoon.append(activity)
        else:
            evening.append(activity)

    # Ensure at least one activity per period using round-robin distribution
    if not morning and activities:
        morning.append(activities[0])
        afternoon = [a for a in afternoon if a != activities[0]]
        evening = [a for a in evening if a != activities[0]]

    structured = {
        "morning": morning,
        "afternoon": afternoon,
        "evening": evening,
        "weather_category": weather_category,
    }
    logger.info(
        "Structured itinerary: morning=%d afternoon=%d evening=%d",
        len(morning),
        len(afternoon),
        len(evening),
    )
    return {**state, "structured_itinerary": structured}
