"""OpenWeatherMap API service with retry logic and fallback data."""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

import httpx

from app.config import settings
from app.schemas.models import WeatherData

logger = logging.getLogger(__name__)

_FALLBACK_WEATHER = WeatherData(
    temperature=22.0,
    condition="Clear",
    humidity=55,
    wind_speed=3.5,
    description="clear sky",
    category="pleasant",
)

_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
_GEO_URL = "https://api.openweathermap.org/geo/1.0/direct"


async def _get_with_retry(client: httpx.AsyncClient, url: str, params: dict, retries: int = 3) -> dict:
    """Execute a GET request with exponential backoff retries."""
    last_exc: Exception = RuntimeError("No attempts made")
    for attempt in range(retries):
        try:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            last_exc = exc
            if attempt < retries - 1:
                await asyncio.sleep(min(2 ** attempt, 10))
    raise last_exc


async def fetch_weather(location: str) -> WeatherData:
    """Fetch current weather for a location from OpenWeatherMap.

    Falls back to default pleasant weather if the API key is missing or
    the request fails after retries.
    """
    if not settings.OPENWEATHER_API_KEY:
        logger.warning("No OPENWEATHER_API_KEY set; using fallback weather data")
        fallback = _FALLBACK_WEATHER.model_copy()
        fallback.description = f"Simulated clear sky for {location}"
        return fallback

    params = {
        "q": location,
        "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric",
    }
    try:
        async with httpx.AsyncClient() as client:
            data = await _get_with_retry(client, _BASE_URL, params)
        return _parse_weather(data)
    except Exception as exc:
        logger.error("Weather fetch failed for %s: %s; using fallback", location, exc)
        return _FALLBACK_WEATHER


async def geocode_location(location: str) -> Optional[dict[str, float]]:
    """Resolve a city name to latitude/longitude coordinates.

    Returns None if the API key is missing or the request fails.
    """
    if not settings.OPENWEATHER_API_KEY:
        logger.warning("No OPENWEATHER_API_KEY; skipping geocoding")
        return None

    params = {
        "q": location,
        "limit": 1,
        "appid": settings.OPENWEATHER_API_KEY,
    }
    try:
        async with httpx.AsyncClient() as client:
            data = await _get_with_retry(client, _GEO_URL, params)
        if data and isinstance(data, list) and len(data) > 0:
            return {"lat": data[0]["lat"], "lon": data[0]["lon"]}
    except Exception as exc:
        logger.error("Geocoding failed for %s: %s", location, exc)
    return None


def _parse_weather(data: dict) -> WeatherData:
    """Parse raw OpenWeatherMap JSON into a WeatherData model."""
    main = data.get("main", {})
    weather_list = data.get("weather", [{}])
    wind = data.get("wind", {})

    condition = weather_list[0].get("main", "Clear") if weather_list else "Clear"
    description = weather_list[0].get("description", "clear sky") if weather_list else "clear sky"
    temperature = float(main.get("temp", 22.0))

    category = _categorize_weather(condition, temperature)

    return WeatherData(
        temperature=temperature,
        condition=condition,
        humidity=int(main.get("humidity", 55)),
        wind_speed=float(wind.get("speed", 3.5)),
        description=description,
        category=category,
    )


def _categorize_weather(condition: str, temperature: float) -> str:
    """Convert weather condition and temperature into a named category."""
    condition_lower = condition.lower()

    if temperature >= 38:
        return "extreme_heat"
    if temperature <= -10:
        return "extreme_cold"
    if "thunderstorm" in condition_lower or "tornado" in condition_lower:
        return "stormy"
    if "snow" in condition_lower or "blizzard" in condition_lower:
        return "snow"
    if "rain" in condition_lower or "drizzle" in condition_lower or "shower" in condition_lower:
        return "rainy"
    if "clear" in condition_lower or "sun" in condition_lower:
        return "sunny"
    return "pleasant"
