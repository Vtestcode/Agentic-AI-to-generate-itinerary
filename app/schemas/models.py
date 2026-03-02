"""Pydantic models and TypedDict state for the itinerary application."""
from __future__ import annotations

from typing import Any, Optional
from typing_extensions import TypedDict

from pydantic import BaseModel, Field


class ItineraryRequest(BaseModel):
    """Request body for generating a new itinerary."""
    location: str = Field(..., description="City or location name")
    preferences: Optional[str] = Field(None, description="Optional travel preferences")


class RefineRequest(BaseModel):
    """Request body for refining an existing itinerary."""
    session_id: str = Field(..., description="Session identifier")
    message: str = Field(..., description="Follow-up message or refinement request")
    previous_itinerary: dict = Field(..., description="Previously generated itinerary")


class WeatherData(BaseModel):
    """Weather information for a location."""
    temperature: float = Field(..., description="Temperature in Celsius")
    condition: str = Field(..., description="Weather condition code/main")
    humidity: int = Field(..., description="Humidity percentage")
    wind_speed: float = Field(..., description="Wind speed in m/s")
    description: str = Field(..., description="Human-readable weather description")
    category: str = Field(default="pleasant", description="Interpreted weather category")


class Activity(BaseModel):
    """A single recommended activity."""
    name: str = Field(..., description="Activity name")
    description: str = Field(..., description="Activity description")
    time_slot: str = Field(..., description="Time slot, e.g. '9:00 AM - 11:00 AM'")
    type: str = Field(..., description="Activity type: indoor or outdoor")
    estimated_duration: str = Field(..., description="Estimated duration, e.g. '2 hours'")


class DayPlan(BaseModel):
    """Activities organized by time of day."""
    morning: list[Activity] = Field(default_factory=list)
    afternoon: list[Activity] = Field(default_factory=list)
    evening: list[Activity] = Field(default_factory=list)


class ItineraryResponse(BaseModel):
    """Full itinerary response returned to the client."""
    location: str
    weather_summary: str
    temperature: float
    recommendations: DayPlan
    tips: list[str] = Field(default_factory=list)


class AgentState(TypedDict, total=False):
    """Shared state dictionary passed between all LangGraph nodes."""
    location: str
    preferences: str
    normalized_location: str
    coordinates: dict[str, float]
    weather_data: dict[str, Any]
    weather_category: str
    raw_activities: list[dict[str, Any]]
    structured_itinerary: dict[str, Any]
    safety_tips: list[str]
    final_response: dict[str, Any]
    error: str
    session_id: str
    previous_itinerary: dict[str, Any]
    refine_message: str
