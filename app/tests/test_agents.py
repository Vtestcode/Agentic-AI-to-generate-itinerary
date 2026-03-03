"""Unit tests for individual agents."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.agents.location_agent import location_node, _normalize_location
from app.agents.weather_agent import weather_node
from app.agents.activity_agent import activity_node, _filter_fallback_activities, _FALLBACK_ACTIVITIES
from app.agents.itinerary_agent import itinerary_node, _slot_to_period
from app.agents.safety_agent import safety_node
from app.schemas.models import WeatherData


# ---------------------------------------------------------------------------
# location_agent tests
# ---------------------------------------------------------------------------

def test_normalize_location_basic():
    assert _normalize_location("  new york  ") == "New York"


def test_normalize_location_with_country():
    assert _normalize_location("paris, france") == "Paris, France"


@pytest.mark.asyncio
async def test_location_node_no_location():
    state = {"location": ""}
    result = await location_node(state)
    assert "error" in result


@pytest.mark.asyncio
async def test_location_node_success():
    with patch("app.agents.location_agent.geocode_location", new_callable=AsyncMock) as mock_geo:
        mock_geo.return_value = {"lat": 48.85, "lon": 2.35}
        state = {"location": "paris"}
        result = await location_node(state)
    assert result["normalized_location"] == "Paris"
    assert result["coordinates"] == {"lat": 48.85, "lon": 2.35}


# ---------------------------------------------------------------------------
# weather_agent tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_weather_node_success():
    mock_weather = WeatherData(
        temperature=20.0,
        condition="Clear",
        humidity=50,
        wind_speed=3.0,
        description="clear sky",
        category="sunny",
    )
    with patch("app.agents.weather_agent.fetch_weather", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_weather
        state = {"normalized_location": "London", "location": "London"}
        result = await weather_node(state)

    assert result["weather_category"] == "sunny"
    assert result["weather_data"]["temperature"] == 20.0


@pytest.mark.asyncio
async def test_weather_node_no_location():
    state = {}
    result = await weather_node(state)
    assert "error" in result


# ---------------------------------------------------------------------------
# activity_agent tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_activity_node_fallback(monkeypatch):
    monkeypatch.setattr("app.agents.activity_agent.settings.OPENAI_API_KEY", "sk-placeholder")
    state = {"normalized_location": "Rome", "weather_category": "sunny", "preferences": ""}
    result = await activity_node(state)
    assert len(result["raw_activities"]) > 0


def test_filter_fallback_rainy():
    result = _filter_fallback_activities("rainy", _FALLBACK_ACTIVITIES)
    # Indoor activities should come first
    assert result[0]["type"] == "indoor"


def test_filter_fallback_sunny():
    result = _filter_fallback_activities("sunny", _FALLBACK_ACTIVITIES)
    assert len(result) == len(_FALLBACK_ACTIVITIES)


# ---------------------------------------------------------------------------
# itinerary_agent tests
# ---------------------------------------------------------------------------

def test_slot_to_period_morning():
    assert _slot_to_period("9:00 AM - 11:00 AM") == "morning"


def test_slot_to_period_afternoon():
    assert _slot_to_period("2:00 PM - 4:00 PM") == "afternoon"


def test_slot_to_period_evening():
    assert _slot_to_period("7:30 PM - 9:00 PM") == "evening"


@pytest.mark.asyncio
async def test_itinerary_node_structures_activities():
    activities = [
        {"name": "A", "description": "d", "time_slot": "9:00 AM - 11:00 AM", "type": "outdoor", "estimated_duration": "2h"},
        {"name": "B", "description": "d", "time_slot": "2:00 PM - 4:00 PM", "type": "indoor", "estimated_duration": "2h"},
        {"name": "C", "description": "d", "time_slot": "7:00 PM - 9:00 PM", "type": "indoor", "estimated_duration": "2h"},
    ]
    state = {"raw_activities": activities, "weather_category": "sunny"}
    result = await itinerary_node(state)
    assert len(result["structured_itinerary"]["morning"]) == 1
    assert len(result["structured_itinerary"]["afternoon"]) == 1
    assert len(result["structured_itinerary"]["evening"]) == 1


# ---------------------------------------------------------------------------
# safety_agent tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_safety_node_extreme_heat_tips():
    state = {
        "structured_itinerary": {"morning": [], "afternoon": [], "evening": []},
        "weather_category": "extreme_heat",
        "weather_data": {"condition": "Clear", "description": "hot", "temperature": 42.0},
        "normalized_location": "Dubai",
        "location": "Dubai",
    }
    result = await safety_node(state)
    tips = result["safety_tips"]
    assert any("water" in t.lower() or "hydrat" in t.lower() for t in tips)


@pytest.mark.asyncio
async def test_safety_node_builds_final_response():
    state = {
        "structured_itinerary": {"morning": [], "afternoon": [], "evening": []},
        "weather_category": "pleasant",
        "weather_data": {"condition": "Clear", "description": "clear sky", "temperature": 22.0},
        "normalized_location": "Sydney",
        "location": "Sydney",
    }
    result = await safety_node(state)
    assert "final_response" in result
    assert result["final_response"]["location"] == "Sydney"
    assert "tips" in result["final_response"]
