from fastapi import APIRouter

from app.api.routes.ingest import router as ingest_router
from app.api.routes.trips import router as trips_router
from app.api.routes.auth import router as auth_router
from app.api.routes.optimize import router as optimize_router
from app.api.routes.itinerary import router as itinerary_router
from app.api.routes.rates import router as rates_router

api_router = APIRouter()
api_router.include_router(ingest_router)
api_router.include_router(trips_router)
api_router.include_router(auth_router)
api_router.include_router(optimize_router)
api_router.include_router(itinerary_router)
api_router.include_router(rates_router)
