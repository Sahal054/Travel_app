#Travelling Salesman: Multimodal Social-to-Spatial Ingestion & Routing Engine
It is a high-performance, asynchronous data pipeline and spatial routing backend. It transforms raw, unstructured social media video URLs (such as Instagram Reels) into precise, verified real-world geographic coordinates, caches them inside a geospatial database, and provides customized, experience-based driving routes containing scenic updates and points of interest (POIs).

## 🏗️ System Architecture

The engine uses an asynchronous job worker execution pattern to decouple long-running network I/O operations (video downloading, AI analysis, and Place verification) from the API layer. This eliminates HTTP gateway timeouts and ensures highly responsive UI feedback.

              [ Incoming Social Media URL ]
                            │
                            ▼
                 ┌───────────────────┐
                 │ FastAPI Endpoint  │ ──► Immediate 202 Accepted (Job ID)
                 └───────────────────┘
                            │
                            ▼
               ┌───────────────────────┐
               │ Async Background Task │
               └───────────────────────┘
                            │
  ┌─────────────────────────┼─────────────────────────┐
  ▼                         ▼                         ▼
┌───────────┐             ┌───────────┐             ┌───────────┐
│  Stream   │             │Multimodal │             │  Spatial  │
│ Scraper   │             │ AI Engine │             │ Resolver  │
│ (yt-dlp)  │             │ (Gemini)  │             │ (Places)  │
└───────────┘             └───────────┘             └───────────┘
│                         │                         │
└─────────────────────────┼─────────────────────────┘
│
▼
┌──────────────────────────┐
│ PostgreSQL / PostGIS DB  │ ◄── Deduplication Check
└──────────────────────────┘


### 🛰️ Experiential Routing Engine (PostGIS Buffer)
When generating a trip route, the engine requests a base path polyline, applies a native spatial **2-kilometer buffer zone** via PostGIS (`ST_DWithin`), filters nearby target venues (e.g., highly rated cafes or historic scenic segments like Munnar's Gap Road), injects them as intermediate waypoints, and compiles a cost-free native deep link.

---

## 🚀 Core Features

- **Asynchronous Processing Pipe:** Accepts incoming ingestion links immediately in `<200ms` via `202 Accepted` status codes while downstream operations compile in background workers.
- **Fast-Validation Deduplication:** Instantly verifies incoming URLs against cached database indices prior to executing multi-stage scraping tasks, dropping API runtime overhead to zero for repeated requests.
- **Multimodal AI Vision & Audio Parsing:** Leverages large multimodal models to inspect local physical landmarks, audio narration, and video on-screen typography to isolate structured text location blocks.
- **Optimized Field-Mask API Integration:** Interacts with the Google Places API (New) utilizing strict query masks to return coordinate maps efficiently at minimal operation tiers.
- **Native Navigation Handoff:** Dynamically maps coordinates into cross-platform Universal Deep Links to launch client turn-by-turn routing inside default device map utilities at zero runtime cost.

---

## 🛠️ Tech Stack

- **Backend Platform:** FastAPI (Python 3.11+, Asyncio)
- **Database Engine:** PostgreSQL + PostGIS Extension
- **Object Relational Mapper:** SQLAlchemy 2.0 & GeoAlchemy2
- **AI Integration:** Google Gemini Multimodal APIs
- **Environment Management:** Docker / Docker Compose

---

## ⚡ Quick Start

### Prerequisites
- Docker and Docker Compose installed.
- Valid API keys for both Google Maps (Places/Routes API) and Gemini.

### 1. Configure Environment Variables
Create a `.env` file within the project root directory:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/roamy_spatial
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_key
