# Travelling Salesman

> **Experiential trip planning powered by social media intelligence.**
> Ingest Instagram Reels → extract real-world locations with AI → plan scenic routes with PostGIS → launch turn-by-turn navigation.

---

## What it does

| Phase | What happens |
|---|---|
| **Phase 1 — Reel Ingestion** | Paste a social media URL. The AI pipeline (Gemini Vision) scrapes the video, identifies the location, verifies it against Google Places, and stores the coordinates in PostGIS. |
| **Phase 2 — Experiential Routing** | Pick an origin and destination. Choose *Scenic* or *Quickest* mode. The backend fetches a Google Routes polyline, runs a PostGIS bounding-box search for scenic POIs along the way, and returns a Google Maps deep link with waypoints injected. |

---

## System Architecture

```
Browser (Next.js)
       │
       │  POST /ingest/reel          POST /api/v1/trips/plan
       ▼                                      ▼
┌──────────────────────────────────────────────────────┐
│                  FastAPI  (async)                    │
│                                                      │
│  ┌─────────────────────┐   ┌────────────────────┐   │
│  │  Ingestion Pipeline  │   │  Routing Engine    │   │
│  │  yt-dlp → Gemini AI  │   │  Google Routes API │   │
│  │  → Google Places     │   │  → PostGIS ST_*    │   │
│  │  → PostGIS INSERT    │   │  → route_cache     │   │
│  └─────────────────────┘   └────────────────────┘   │
└──────────────────────────────────────────────────────┘
                        │
              ┌─────────┴──────────┐
              │  PostgreSQL/PostGIS │
              │  places            │
              │  saved_reels       │
              │  route_cache       │
              └────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, TypeScript, Tailwind CSS, MapLibre GL JS, react-map-gl |
| Map tiles | OpenFreeMap (open source, no API key) |
| Backend | FastAPI, Python 3.11+, asyncio |
| Database | PostgreSQL 16 + PostGIS 3.4 |
| ORM | SQLAlchemy 2.0, GeoAlchemy2, Alembic |
| AI | Google Gemini (multimodal vision + audio) |
| Routing | Google Routes API v2 |
| Places | Google Places API (New) |
| Runtime | Docker, Docker Compose |

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Google Cloud project with **Routes API**, **Places API (New)**, and **Gemini API** enabled
- A Gemini API key and a Google Maps API key

### 1. Clone and configure

```bash
git clone https://github.com/your-username/TravelApp.git
cd TravelApp
```

Create `.env` in the project root:

```env
DATABASE_URL=postgresql+asyncpg://roamy:roamy@db:5432/roamy
GEMINI_API_KEY=AIza...
GOOGLE_MAPS_API_KEY=AIza...
LOG_LEVEL=INFO
```

Create `.env.db` in the project root:

```env
POSTGRES_USER=roamy
POSTGRES_PASSWORD=roamy
POSTGRES_DB=roamy
```

### 2. Start the backend

```bash
docker compose up --build -d
docker compose run --rm api alembic upgrade head
```

API is live at **http://localhost:8000** · Swagger UI at **http://localhost:8000/docs**

### 3. Start the frontend

```bash
cd frontend
cp .env.local.example .env.local   # or create it manually (see below)
npm install
npm run dev
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Frontend is live at **http://localhost:3000**

---

## API Reference

### `POST /ingest/reel`

Ingest a social media reel and extract its location.

```json
// Request
{ "reel_url": "https://www.instagram.com/reel/ABC123/" }

// Response 202
{
  "status": "accepted",
  "saved_reel_id": 42,
  "place_id": 7,
  "place_summary": {
    "place_name": "Vattavada",
    "formatted_address": "Vattavada, Kerala, India",
    "latitude": 10.1777,
    "longitude": 77.2537,
    "confidence": 0.97
  }
}
```

### `POST /api/v1/trips/plan`

Plan a route between two coordinates.

```json
// Request
{
  "origin_lat": 10.17,
  "origin_lng": 77.25,
  "dest_lat": 9.58,
  "dest_lng": 77.07,
  "route_mode": "scenic"
}

// Response
{
  "route_status": "OK",
  "injected_waypoints_count": 1,
  "injected_poi_names": ["Munnar Tea Gardens"],
  "native_maps_url": "https://www.google.com/maps/dir/?api=1&origin=...",
  "waypoints": [{ "name": "Munnar Tea Gardens", "lat": 10.08, "lng": 77.06, "poi_type": "scenic_viewpoint" }],
  "cache_hit": false
}
```

**Route modes:**

| Mode | Behaviour |
|---|---|
| `scenic` | Calls Google Routes with `avoidHighways: true`, then runs a PostGIS bounding-box macro search for `scenic_viewpoint`, `scenic_road`, or `tourist_attraction` POIs. Injects up to 1 scenic anchor. |
| `quickest` | Returns the fastest Google Routes polyline directly. No PostGIS query. |

Both modes check and populate the `route_cache` table (SHA-256 hash of snapped coordinates + mode) to avoid duplicate Google API calls.

---

## Project Structure

```
TravelApp/
├── app/                        # FastAPI application
│   ├── api/routes/
│   │   ├── ingest.py           # POST /ingest/reel
│   │   └── trips.py            # POST /api/v1/trips/plan
│   ├── models/
│   │   ├── place.py            # PostGIS Geography(POINT) column
│   │   ├── saved_reel.py
│   │   └── route_cache.py      # SHA-256 polyline cache
│   ├── services/
│   │   ├── routing.py          # Google Routes + PostGIS bounding box
│   │   └── ingestion_service.py
│   └── core/config.py
├── alembic/versions/           # DB migrations
├── frontend/                   # Next.js 15 app
│   └── src/
│       ├── app/
│       │   ├── page.tsx        # Trip planner (reads ?dest_lat/lng from URL)
│       │   └── ingest/page.tsx # Reel ingestion
│       ├── components/
│       │   ├── MapCanvas.tsx         # MapLibre map + trip state
│       │   ├── TripPlannerPanel.tsx  # Route form + results
│       │   ├── IngestMapCanvas.tsx   # Map for ingest page
│       │   ├── IngestPanel.tsx       # URL input + AI results
│       │   ├── WaypointMarker.tsx    # Animated scenic pin
│       │   └── NavBar.tsx            # Plan Trip ↔ Ingest Reel tabs
│       └── lib/
│           ├── api.ts          # planTrip(), ingestReel()
│           └── types.ts        # Mirrors backend Pydantic schemas
├── docker-compose.yml
└── requirements.txt
```

---

## User Flow

```
1. /ingest  →  Paste Instagram / TikTok / YouTube Shorts URL
               ↓
               AI extracts location (up to ~30s)
               ↓
               Pink marker appears on map at extracted place
               ↓
               Click "Plan a Route Here →"

2. /        →  Destination pre-filled with extracted coordinates
               Add an origin (or use "Use my location")
               Choose Scenic or Quickest
               ↓
               Click "Plan My Route"
               ↓
               Emerald markers appear for scenic waypoints
               ↓
               Click "Open in Google Maps →"  ← universal deep link
```

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| `Geography(POINT, 4326)` for `places.location` | `ST_DWithin` on geography types accepts metres natively — no `ST_Transform` needed |
| `ST_MakeEnvelope` + `ST_Expand` for scenic search | Broader bounding-box catches POIs on curved routes that extend outside the straight-line A→B box |
| SHA-256 hash with 3 d.p. coordinate snapping | ~111 m grid precision eliminates duplicate Google API calls for nearby but not identical requests |
| `react-map-gl/maplibre` + OpenFreeMap tiles | Zero API key, zero cost, fully open-source map stack |
| `avoidHighways: true` for scenic mode | Forces Google Routes onto local roads where scenic POIs are concentrated |

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | ✅ | PostgreSQL asyncpg connection string |
| `GEMINI_API_KEY` | ✅ | Google Gemini API key |
| `GOOGLE_MAPS_API_KEY` | ✅ | Google Maps key (Routes API + Places API enabled) |
| `ALLOWED_ORIGINS` | optional | CORS origins (default: `["http://localhost:3000"]`) |
| `LOG_LEVEL` | optional | `INFO` / `DEBUG` / `WARNING` |
| `NEXT_PUBLIC_API_URL` | ✅ (frontend) | Backend base URL |

---

## License

MIT
