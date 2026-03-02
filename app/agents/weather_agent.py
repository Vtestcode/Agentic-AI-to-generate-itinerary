"""Weather agent: fetches live weather and interprets it into a category."""
from __future__ import annotations

import logging

from app.schemas.models import AgentState
from app.services.weather_service import fetch_weather

logger = logging.getLogger(__name__)


async def weather_node(state: AgentState) -> AgentState:
    """Fetch current weather for the normalized location and store in state."""
    location = state.get("normalized_location") or state.get("location", "")
    if not location:
        return {**state, "error": "No location available for weather lookup"}

    weather_data = await fetch_weather(location)
    logger.info(
        "Weather for %s: %s %.1f°C (category: %s)",
        location,
        weather_data.condition,
        weather_data.temperature,
        weather_data.category,
    )

    return {
        **state,
        "weather_data": weather_data.model_dump(),
        "weather_category": weather_data.category,
    }
