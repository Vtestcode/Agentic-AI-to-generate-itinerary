"""LangGraph workflow orchestrating all travel itinerary agents."""
from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import StateGraph, END

from app.agents.location_agent import location_node
from app.agents.weather_agent import weather_node
from app.agents.activity_agent import activity_node
from app.agents.itinerary_agent import itinerary_node
from app.agents.safety_agent import safety_node
from app.schemas.models import AgentState

logger = logging.getLogger(__name__)


def build_workflow() -> Any:
    """Construct and compile the LangGraph StateGraph for itinerary generation."""
    graph = StateGraph(AgentState)

    graph.add_node("location_node", location_node)
    graph.add_node("weather_node", weather_node)
    graph.add_node("activity_node", activity_node)
    graph.add_node("itinerary_node", itinerary_node)
    graph.add_node("safety_node", safety_node)

    graph.set_entry_point("location_node")
    graph.add_edge("location_node", "weather_node")
    graph.add_edge("weather_node", "activity_node")
    graph.add_edge("activity_node", "itinerary_node")
    graph.add_edge("itinerary_node", "safety_node")
    graph.add_edge("safety_node", END)

    return graph.compile()


async def run_itinerary_workflow(location: str, preferences: str = "") -> dict[str, Any]:
    """Run the full itinerary generation workflow for a given location.

    Returns the final_response dict from AgentState.
    """
    workflow = build_workflow()
    initial_state: AgentState = {
        "location": location,
        "preferences": preferences,
    }
    logger.info("Starting itinerary workflow for: %s", location)
    result = await workflow.ainvoke(initial_state)
    if "error" in result and result["error"]:
        logger.error("Workflow error: %s", result["error"])
    return result.get("final_response", {})


async def run_refine_workflow(
    location: str,
    preferences: str,
    previous_itinerary: dict[str, Any],
    refine_message: str,
    session_id: str = "",
) -> dict[str, Any]:
    """Run the refinement workflow incorporating previous itinerary context.

    For simplicity, re-runs the full workflow with the refinement message
    appended to preferences so the LLM can adjust its suggestions accordingly.
    """
    combined_preferences = preferences
    if refine_message:
        combined_preferences = f"{preferences} | Refinement request: {refine_message}".strip(" |")

    workflow = build_workflow()
    initial_state: AgentState = {
        "location": location,
        "preferences": combined_preferences,
        "previous_itinerary": previous_itinerary,
        "session_id": session_id,
        "refine_message": refine_message,
    }
    logger.info("Starting refinement workflow for session: %s", session_id)
    result = await workflow.ainvoke(initial_state)
    return result.get("final_response", {})
