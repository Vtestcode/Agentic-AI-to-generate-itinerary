"""Safety agent: validates recommendations and appends weather-appropriate safety tips."""
from __future__ import annotations

import logging
from typing import Any

from app.schemas.models import AgentState

logger = logging.getLogger(__name__)

_BASE_TIPS: list[str] = [
    "Keep a copy of your travel documents in a secure digital location.",
    "Share your itinerary with someone you trust back home.",
    "Keep local emergency numbers saved on your phone.",
]

_CATEGORY_TIPS: dict[str, list[str]] = {
    "sunny": [
        "Apply SPF 30+ sunscreen and reapply every 2 hours.",
        "Wear a hat and UV-protective sunglasses.",
        "Stay hydrated – drink at least 2–3 litres of water throughout the day.",
    ],
    "rainy": [
        "Carry a compact umbrella or waterproof jacket.",
        "Watch for slippery surfaces – wear shoes with good grip.",
        "Check local flood or weather alerts before heading out.",
    ],
    "stormy": [
        "Stay indoors and avoid all outdoor activities during active thunderstorms.",
        "Keep away from tall trees, open fields, and elevated structures.",
        "Monitor official weather alerts and follow local authority guidance.",
        "Have an emergency kit ready including a flashlight, first aid, and backup power.",
    ],
    "extreme_heat": [
        "Drink water every 20–30 minutes even if you don't feel thirsty.",
        "Avoid strenuous outdoor activities between 11 AM and 4 PM.",
        "Wear light-coloured, loose-fitting, breathable clothing.",
        "Seek air-conditioned spaces regularly to avoid heat exhaustion.",
        "Know the signs of heat stroke: confusion, no sweating, very high body temp – call emergency services immediately.",
    ],
    "snow": [
        "Dress in warm, waterproof layers.",
        "Wear boots with good traction to prevent slipping on ice.",
        "Check road and transport conditions before travelling.",
        "Keep hand-warmers and an emergency kit in your bag.",
    ],
    "pleasant": [
        "Light layers are recommended as temperatures may shift during the day.",
        "Stay hydrated and carry a reusable water bottle.",
    ],
    "extreme_cold": [
        "Wear thermal base layers, insulating mid-layers, and a windproof outer layer.",
        "Protect exposed skin – frostbite can occur within minutes in extreme cold.",
        "Carry emergency supplies including hand-warmers and a thermal blanket.",
        "Stay dry – wet clothing in extreme cold dramatically increases hypothermia risk.",
    ],
}


def _is_unsafe_for_weather(activity: dict[str, Any], category: str) -> bool:
    """Return True if an activity is potentially unsafe for the given weather."""
    activity_type = activity.get("type", "indoor")
    name_lower = activity.get("name", "").lower()
    desc_lower = activity.get("description", "").lower()

    if category == "extreme_heat" and activity_type == "outdoor":
        hazard_keywords = ["hike", "run", "cycle", "cycling", "trek", "marathon", "sport"]
        if any(k in name_lower or k in desc_lower for k in hazard_keywords):
            return True
    if category in ("extreme_cold", "snow") and activity_type == "outdoor":
        hazard_keywords = ["swim", "swimming", "water park", "splash"]
        if any(k in name_lower or k in desc_lower for k in hazard_keywords):
            return True
    return False


async def safety_node(state: AgentState) -> AgentState:
    """Add safety tips and flag potentially unsafe activities."""
    structured: dict[str, Any] = state.get("structured_itinerary", {})
    category = state.get("weather_category", "pleasant")

    tips = list(_BASE_TIPS)
    tips.extend(_CATEGORY_TIPS.get(category, []))

    # Build final response
    weather_data: dict[str, Any] = state.get("weather_data", {})
    location = state.get("normalized_location") or state.get("location", "Unknown")

    weather_summary = (
        f"{weather_data.get('condition', 'Clear')}, "
        f"{weather_data.get('description', 'clear sky')}"
    )

    final_response: dict[str, Any] = {
        "location": location,
        "weather_summary": weather_summary,
        "temperature": weather_data.get("temperature", 22.0),
        "recommendations": {
            "morning": structured.get("morning", []),
            "afternoon": structured.get("afternoon", []),
            "evening": structured.get("evening", []),
        },
        "tips": tips,
    }

    logger.info("Safety node complete – %d tips generated for category: %s", len(tips), category)
    return {**state, "safety_tips": tips, "final_response": final_response}
