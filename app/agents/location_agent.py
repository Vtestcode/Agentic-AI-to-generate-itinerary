"""Location agent: validates, normalizes, and geocodes the user-supplied location."""
from __future__ import annotations

import logging

from app.schemas.models import AgentState
from app.services.weather_service import geocode_location

logger = logging.getLogger(__name__)


async def location_node(state: AgentState) -> AgentState:
    """Validate and normalize the input location, then resolve its coordinates.

    Stores normalized_location and coordinates (if available) back into state.
    """
    location: str = state.get("location", "").strip()
    if not location:
        logger.error("No location provided in state")
        return {**state, "error": "Location is required"}

    normalized = _normalize_location(location)
    logger.info("Normalized location: %s -> %s", location, normalized)

    coords = await geocode_location(normalized)
    if coords:
        logger.info("Resolved coordinates for %s: %s", normalized, coords)
    else:
        logger.warning("Could not geocode %s; proceeding without coordinates", normalized)

    return {
        **state,
        "normalized_location": normalized,
        "coordinates": coords or {},
    }


def _normalize_location(location: str) -> str:
    """Normalize a location string: title-case, strip extra whitespace."""
    parts = [part.strip().title() for part in location.split(",")]
    return ", ".join(parts)
