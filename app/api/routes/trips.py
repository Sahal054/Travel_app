import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.core.config import settings
from app.schemas.trips import TripPlanRequest, TripPlanResponse
from app.services.routing import fetch_encoded_polyline, fetch_pois_along_route, build_maps_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/trips", tags=["trips"])


@router.post("/plan", response_model=TripPlanResponse)
async def plan_trip(
    payload: TripPlanRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TripPlanResponse:
    """
    Plan an experiential route:
    1. Fetch a driving polyline from Google Routes API.
    2. Find POIs within the search radius of that route via PostGIS.
    3. Return a Google Maps deep link with the discovered POIs as waypoints.
    """

    if not settings.google_maps_api_key:
        raise HTTPException(
            status_code=503,
            detail="GOOGLE_MAPS_API_KEY is not configured on this server.",
        )

    logger.info(
        "Planning trip",
        extra={
            "event": "trip_plan_start",
            "origin": f"{payload.origin_lat},{payload.origin_lng}",
            "destination": f"{payload.dest_lat},{payload.dest_lng}",
            "poi_type": payload.poi_type,
            "radius_m": payload.search_radius_meters,
        },
    )

    # Step 1 — Driving polyline from Google Routes API
    encoded_polyline = await fetch_encoded_polyline(
        origin_lat=payload.origin_lat,
        origin_lng=payload.origin_lng,
        dest_lat=payload.dest_lat,
        dest_lng=payload.dest_lng,
        api_key=settings.google_maps_api_key,
    )

    # Step 2 — PostGIS spatial buffer query along the polyline
    waypoints = await fetch_pois_along_route(
        db=db,
        encoded_polyline=encoded_polyline,
        search_radius_meters=payload.search_radius_meters,
        poi_type=payload.poi_type,
    )

    # Step 3 — Google Maps universal deep link
    maps_url = build_maps_url(
        origin_lat=payload.origin_lat,
        origin_lng=payload.origin_lng,
        dest_lat=payload.dest_lat,
        dest_lng=payload.dest_lng,
        waypoints=waypoints,
    )

    logger.info(
        "Trip planned",
        extra={
            "event": "trip_plan_complete",
            "waypoints_injected": len(waypoints),
        },
    )

    return TripPlanResponse(
        route_status="OK",
        injected_waypoints_count=len(waypoints),
        injected_poi_names=[wp.name for wp in waypoints],
        native_maps_url=maps_url,
        waypoints=waypoints,
    )
