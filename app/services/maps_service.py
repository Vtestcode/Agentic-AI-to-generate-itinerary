"""Optional Google Places API integration for nearby place discovery."""
from __future__ import annotations

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_PLACES_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"


async def fetch_nearby_places(
    lat: float, lon: float, radius: int = 5000, place_type: str = "tourist_attraction"
) -> list[dict]:
    """Fetch nearby places from Google Places API.

    Returns an empty list if the API key is absent or the request fails.
    """
    if not settings.GOOGLE_PLACES_API_KEY:
        logger.info("No GOOGLE_PLACES_API_KEY; skipping Places lookup")
        return []

    params = {
        "location": f"{lat},{lon}",
        "radius": radius,
        "type": place_type,
        "key": settings.GOOGLE_PLACES_API_KEY,
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(_PLACES_URL, params=params)
            response.raise_for_status()
            data = response.json()
        results = data.get("results", [])
        return [
            {
                "name": p.get("name", ""),
                "rating": p.get("rating", 0),
                "vicinity": p.get("vicinity", ""),
                "types": p.get("types", []),
            }
            for p in results[:10]
        ]
    except Exception as exc:
        logger.error("Google Places request failed: %s", exc)
        return []
