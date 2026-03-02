"""Unit tests for weather and maps services."""
from __future__ import annotations

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.weather_service import fetch_weather, geocode_location, _parse_weather
from app.schemas.models import WeatherData


SAMPLE_WEATHER_RESPONSE = {
    "main": {"temp": 25.0, "humidity": 60},
    "weather": [{"main": "Clear", "description": "clear sky"}],
    "wind": {"speed": 4.0},
}

SAMPLE_GEO_RESPONSE = [{"lat": 51.5074, "lon": -0.1278, "name": "London"}]


@pytest.mark.asyncio
async def test_fetch_weather_success(monkeypatch):
    """fetch_weather returns parsed WeatherData on successful API call."""
    monkeypatch.setattr("app.services.weather_service.settings.OPENWEATHER_API_KEY", "test-key")

    mock_response = MagicMock()
    mock_response.json.return_value = SAMPLE_WEATHER_RESPONSE
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("app.services.weather_service.httpx.AsyncClient", return_value=mock_client):
        result = await fetch_weather("London")

    assert isinstance(result, WeatherData)
    assert result.temperature == 25.0
    assert result.condition == "Clear"
    assert result.humidity == 60
    assert result.category == "sunny"


@pytest.mark.asyncio
async def test_fetch_weather_fallback_no_key(monkeypatch):
    """fetch_weather returns fallback data when API key is missing."""
    monkeypatch.setattr("app.services.weather_service.settings.OPENWEATHER_API_KEY", "")
    result = await fetch_weather("Paris")
    assert isinstance(result, WeatherData)
    assert result.temperature == 22.0


@pytest.mark.asyncio
async def test_fetch_weather_fallback_on_error(monkeypatch):
    """fetch_weather returns fallback data when the HTTP request fails."""
    monkeypatch.setattr("app.services.weather_service.settings.OPENWEATHER_API_KEY", "test-key")

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

    with patch("app.services.weather_service.httpx.AsyncClient", return_value=mock_client):
        result = await fetch_weather("Tokyo")

    assert isinstance(result, WeatherData)
    assert result.temperature == 22.0


@pytest.mark.asyncio
async def test_geocode_location_success(monkeypatch):
    """geocode_location returns lat/lon dict on success."""
    monkeypatch.setattr("app.services.weather_service.settings.OPENWEATHER_API_KEY", "test-key")

    mock_response = MagicMock()
    mock_response.json.return_value = SAMPLE_GEO_RESPONSE
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("app.services.weather_service.httpx.AsyncClient", return_value=mock_client):
        result = await geocode_location("London")

    assert result == {"lat": 51.5074, "lon": -0.1278}


@pytest.mark.asyncio
async def test_geocode_location_no_key(monkeypatch):
    """geocode_location returns None when API key is absent."""
    monkeypatch.setattr("app.services.weather_service.settings.OPENWEATHER_API_KEY", "")
    result = await geocode_location("Berlin")
    assert result is None


def test_parse_weather_categorize_rainy():
    """_parse_weather correctly categorises rainy conditions."""
    data = {
        "main": {"temp": 15.0, "humidity": 85},
        "weather": [{"main": "Rain", "description": "light rain"}],
        "wind": {"speed": 5.0},
    }
    result = _parse_weather(data)
    assert result.category == "rainy"


def test_parse_weather_categorize_extreme_heat():
    """_parse_weather correctly categorises extreme heat."""
    data = {
        "main": {"temp": 42.0, "humidity": 30},
        "weather": [{"main": "Clear", "description": "clear sky"}],
        "wind": {"speed": 2.0},
    }
    result = _parse_weather(data)
    assert result.category == "extreme_heat"


def test_parse_weather_categorize_snow():
    """_parse_weather correctly categorises snowy conditions."""
    data = {
        "main": {"temp": -2.0, "humidity": 70},
        "weather": [{"main": "Snow", "description": "light snow"}],
        "wind": {"speed": 3.0},
    }
    result = _parse_weather(data)
    assert result.category == "snow"
