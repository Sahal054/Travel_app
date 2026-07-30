from fastapi import APIRouter

from app.api.routes.ingest import router as ingest_router
from app.api.routes.trips import router as trips_router

api_router = APIRouter()
api_router.include_router(ingest_router)
api_router.include_router(trips_router)
