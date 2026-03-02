# ✈️ Agentic AI Travel Itinerary Generator

A production-ready agentic AI application that generates personalized travel itineraries using **LangGraph**, **LangChain**, **OpenAI GPT-4o-mini**, and **FastAPI**.

## Features

- 🤖 **Multi-agent pipeline** – Location → Weather → Activity → Itinerary → Safety nodes
- 🌦️ **Live weather integration** – OpenWeatherMap API with automatic fallback
- 🗺️ **Google Places support** – Optional nearby place discovery
- 💬 **Itinerary refinement** – Follow-up messages to adjust recommendations
- 🛡️ **Safety tips** – Weather-appropriate travel advice
- 🖥️ **Modern frontend** – Clean HTML/CSS/JS UI served alongside the API
- 🐳 **Docker-ready** – Single-command deployment

## Quick Start

### 1. Clone and configure
```bash
git clone <repo-url>
cd Agentic-AI-to-generate-itinerary
cp .env.example .env
# Edit .env and add your API keys
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the server
```bash
uvicorn app.main:app --reload
```

Open http://localhost:8000 in your browser.

### 4. Docker
```bash
docker-compose up --build
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/itinerary` | Generate a new itinerary |
| POST | `/itinerary/refine` | Refine an existing itinerary |
| GET | `/docs` | Interactive Swagger UI |

### Generate Itinerary
```bash
curl -X POST http://localhost:8000/itinerary \
  -H "Content-Type: application/json" \
  -d '{"location": "Paris", "preferences": "museums and local food"}'
```

### Refine Itinerary
```bash
curl -X POST http://localhost:8000/itinerary/refine \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc123",
    "message": "Replace lunch with a cooking class",
    "previous_itinerary": { ... }
  }'
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for GPT-4o-mini |
| `OPENWEATHER_API_KEY` | No | OpenWeatherMap key (fallback weather used if absent) |
| `GOOGLE_PLACES_API_KEY` | No | Google Places key (skipped if absent) |
| `LOG_LEVEL` | No | Logging level (default: INFO) |

## Architecture

```
Request
  │
  ▼
FastAPI (app/main.py)
  │
  ▼
LangGraph Workflow (app/agents/workflow.py)
  │
  ├─► location_node   – Validate & geocode location
  ├─► weather_node    – Fetch live weather data
  ├─► activity_node   – LLM-generated activity suggestions
  ├─► itinerary_node  – Structure activities by time of day
  └─► safety_node     – Add safety tips & build final response
```

## Running Tests

```bash
pytest app/tests/ -v
```

## Project Structure

```
├── app/
│   ├── agents/          # LangGraph agent nodes
│   │   ├── workflow.py  # Graph definition
│   │   ├── location_agent.py
│   │   ├── weather_agent.py
│   │   ├── activity_agent.py
│   │   ├── itinerary_agent.py
│   │   └── safety_agent.py
│   ├── services/        # External API integrations
│   │   ├── weather_service.py
│   │   └── maps_service.py
│   ├── schemas/         # Pydantic models & TypedDict state
│   │   └── models.py
│   ├── tests/           # pytest test suite
│   └── main.py          # FastAPI application
├── frontend/
│   └── index.html       # Single-page frontend
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## License

MIT