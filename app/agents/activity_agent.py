"""Activity agent: uses an LLM to recommend activities based on weather and location."""
from __future__ import annotations

import json
import logging
from typing import Any

from app.config import settings
from app.schemas.models import AgentState

logger = logging.getLogger(__name__)

_WEATHER_PROMPTS: dict[str, str] = {
    "sunny": "sunny and perfect for outdoor activities",
    "rainy": "rainy – indoor activities and covered venues are preferred",
    "stormy": "stormy with thunderstorms – indoor activities only, avoid outdoor exposure",
    "extreme_heat": "extremely hot – shaded or air-conditioned venues are essential",
    "snow": "snowy – cozy indoor experiences or scenic winter spots",
    "pleasant": "pleasantly mild and great for a mix of indoor and outdoor activities",
    "extreme_cold": "extremely cold – warm indoor venues are strongly preferred",
}

_FALLBACK_ACTIVITIES: list[dict[str, Any]] = [
    {
        "name": "City Walking Tour",
        "description": "Explore the city's historic center on foot with a knowledgeable guide.",
        "time_slot": "9:00 AM - 11:00 AM",
        "type": "outdoor",
        "estimated_duration": "2 hours",
    },
    {
        "name": "Local Museum",
        "description": "Discover the region's art, history, and culture at the main municipal museum.",
        "time_slot": "11:30 AM - 1:30 PM",
        "type": "indoor",
        "estimated_duration": "2 hours",
    },
    {
        "name": "Traditional Lunch",
        "description": "Enjoy authentic local cuisine at a highly-rated restaurant in the city center.",
        "time_slot": "1:30 PM - 3:00 PM",
        "type": "indoor",
        "estimated_duration": "1.5 hours",
    },
    {
        "name": "Botanical Garden",
        "description": "Stroll through beautifully maintained gardens with local and exotic plants.",
        "time_slot": "3:30 PM - 5:00 PM",
        "type": "outdoor",
        "estimated_duration": "1.5 hours",
    },
    {
        "name": "Sunset Viewpoint",
        "description": "Catch a breathtaking sunset from the city's most iconic viewpoint.",
        "time_slot": "6:00 PM - 7:00 PM",
        "type": "outdoor",
        "estimated_duration": "1 hour",
    },
    {
        "name": "Evening Dining",
        "description": "Savour a relaxing dinner at a local favourite featuring regional specialties.",
        "time_slot": "7:30 PM - 9:00 PM",
        "type": "indoor",
        "estimated_duration": "1.5 hours",
    },
]


async def activity_node(state: AgentState) -> AgentState:
    """Generate activity recommendations using an LLM or fallback list."""
    location = state.get("normalized_location") or state.get("location", "Unknown")
    weather_category = state.get("weather_category", "pleasant")
    preferences = state.get("preferences") or ""
    weather_desc = _WEATHER_PROMPTS.get(weather_category, "generally fine")

    activities = await _generate_activities(location, weather_desc, weather_category, preferences)
    logger.info("Generated %d activities for %s", len(activities), location)
    return {**state, "raw_activities": activities}


async def _generate_activities(
    location: str, weather_desc: str, weather_category: str, preferences: str
) -> list[dict[str, Any]]:
    """Call the LLM for activity suggestions, falling back to static data on error."""
    if settings.OPENAI_API_KEY == "sk-placeholder" or not settings.OPENAI_API_KEY:
        logger.warning("No OpenAI API key; using fallback activities")
        return _filter_fallback_activities(weather_category, _FALLBACK_ACTIVITIES)

    try:
        from langchain_openai import ChatOpenAI
        from langchain.schema import HumanMessage, SystemMessage

        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            openai_api_key=settings.OPENAI_API_KEY,
        )

        pref_line = f"Traveller preferences: {preferences}" if preferences else ""
        system = (
            "You are an expert travel planner. Always respond with valid JSON only – "
            "a JSON array of activity objects. Each object must have exactly these fields: "
            "name (string), description (string), time_slot (string), type ('indoor' or 'outdoor'), "
            "estimated_duration (string)."
        )
        human = (
            f"Create 6 activities for a traveller visiting {location}. "
            f"The weather is {weather_desc}. {pref_line} "
            "Provide a balanced day with morning, afternoon, and evening activities. "
            "Respond with a JSON array only, no markdown fences."
        )

        response = await llm.ainvoke([SystemMessage(content=system), HumanMessage(content=human)])
        raw = response.content.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        activities: list[dict] = json.loads(raw)
        return activities
    except Exception as exc:
        logger.error("LLM activity generation failed: %s; using fallback", exc)
        return _filter_fallback_activities(weather_category, _FALLBACK_ACTIVITIES)


def _filter_fallback_activities(
    category: str, activities: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Filter fallback activities to match the weather category."""
    if category in ("rainy", "stormy", "extreme_heat", "extreme_cold"):
        return [a for a in activities if a["type"] == "indoor"] + [
            a for a in activities if a["type"] == "outdoor"
        ]
    return activities
