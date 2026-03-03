"""FastAPI application entry point."""
from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.schemas.models import ItineraryRequest, RefineRequest, ItineraryResponse
from app.agents.workflow import run_itinerary_workflow, run_refine_workflow

# Configure root logger
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agentic AI Travel Itinerary",
    description="Generate personalised travel itineraries powered by LangGraph and OpenAI",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict:
    """Return service health status."""
    return {"status": "ok", "service": "Agentic AI Travel Itinerary"}


@app.post("/itinerary", response_model=ItineraryResponse)
async def generate_itinerary(request: ItineraryRequest) -> ItineraryResponse:
    """Generate a full day itinerary for the given location and preferences."""
    logger.info("Generating itinerary for location=%s", request.location)
    try:
        result = await run_itinerary_workflow(
            location=request.location,
            preferences=request.preferences or "",
        )
        if not result:
            raise HTTPException(status_code=500, detail="Itinerary generation failed")
        return ItineraryResponse(**result)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error generating itinerary: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/itinerary/refine", response_model=ItineraryResponse)
async def refine_itinerary(request: RefineRequest) -> ItineraryResponse:
    """Refine an existing itinerary based on a follow-up message."""
    logger.info("Refining itinerary for session=%s", request.session_id)
    try:
        previous = request.previous_itinerary
        location = previous.get("location", "")
        if not location:
            raise HTTPException(status_code=400, detail="previous_itinerary must contain a location")

        result = await run_refine_workflow(
            location=location,
            preferences="",
            previous_itinerary=previous,
            refine_message=request.message,
            session_id=request.session_id,
        )
        if not result:
            raise HTTPException(status_code=500, detail="Itinerary refinement failed")
        return ItineraryResponse(**result)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error refining itinerary: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
