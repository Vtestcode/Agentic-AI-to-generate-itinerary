"""Unit tests for FastAPI endpoints."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

_MOCK_ITINERARY = {
    "location": "London",
    "weather_summary": "Clear, clear sky",
    "temperature": 18.0,
    "recommendations": {
        "morning": [
            {
                "name": "Tower Bridge",
                "description": "Visit the iconic bridge.",
                "time_slot": "9:00 AM - 11:00 AM",
                "type": "outdoor",
                "estimated_duration": "2 hours",
            }
        ],
        "afternoon": [
            {
                "name": "British Museum",
                "description": "World-class museum.",
                "time_slot": "1:00 PM - 3:00 PM",
                "type": "indoor",
                "estimated_duration": "2 hours",
            }
        ],
        "evening": [
            {
                "name": "West End Show",
                "description": "A fantastic theatre experience.",
                "time_slot": "7:30 PM - 10:00 PM",
                "type": "indoor",
                "estimated_duration": "2.5 hours",
            }
        ],
    },
    "tips": ["Stay hydrated.", "Keep documents safe."],
}


def test_health_check():
    """GET /health returns 200 with status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_generate_itinerary_success():
    """POST /itinerary returns 200 with itinerary data."""
    with patch(
        "app.main.run_itinerary_workflow",
        new_callable=AsyncMock,
        return_value=_MOCK_ITINERARY,
    ):
        response = client.post("/itinerary", json={"location": "London", "preferences": "museums"})
    assert response.status_code == 200
    data = response.json()
    assert data["location"] == "London"
    assert "recommendations" in data
    assert "morning" in data["recommendations"]


def test_generate_itinerary_missing_location():
    """POST /itinerary without location returns 422."""
    response = client.post("/itinerary", json={"preferences": "beaches"})
    assert response.status_code == 422


def test_generate_itinerary_workflow_failure():
    """POST /itinerary returns 500 when workflow returns empty result."""
    with patch(
        "app.main.run_itinerary_workflow",
        new_callable=AsyncMock,
        return_value={},
    ):
        response = client.post("/itinerary", json={"location": "London"})
    assert response.status_code == 500


def test_refine_itinerary_success():
    """POST /itinerary/refine returns 200 with refined itinerary."""
    with patch(
        "app.main.run_refine_workflow",
        new_callable=AsyncMock,
        return_value=_MOCK_ITINERARY,
    ):
        response = client.post(
            "/itinerary/refine",
            json={
                "session_id": "abc123",
                "message": "Add more outdoor activities",
                "previous_itinerary": _MOCK_ITINERARY,
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert data["location"] == "London"


def test_refine_itinerary_missing_location():
    """POST /itinerary/refine returns 400 when previous_itinerary has no location."""
    with patch(
        "app.main.run_refine_workflow",
        new_callable=AsyncMock,
        return_value=_MOCK_ITINERARY,
    ):
        response = client.post(
            "/itinerary/refine",
            json={
                "session_id": "abc123",
                "message": "More activities",
                "previous_itinerary": {"weather_summary": "Clear"},
            },
        )
    assert response.status_code == 400
