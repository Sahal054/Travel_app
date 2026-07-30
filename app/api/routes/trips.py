import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db_session
from app.schemas.trips import RouteMode, TripPlanRequest, TripPlanResponse
from app.services.routing import (
    build_maps_url,
    compute_route_hash,
    fetch_encoded_polyline,
    fetch_scenic_anchor,
    get_cached_polyline,
    save_route_cache,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/trips", tags=["trips"])


@router.post("/plan", response_model=TripPlanResponse)
async def plan_trip(
    payload: TripPlanRequest,
    db: AsyncSession = Depends(get_db_session),
) -> TripPlanResponse:
    """
    Plan a trip with route branching:
    - quickest: Google Routes polyline, no PostGIS, 0 waypoints.
    - scenic:   Google Routes polyline (avoidHighways) + PostGIS bounding-box
                macro search for a single scenic anchor waypoint.
    Both modes check/populate the route_cache table before calling Google.
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
            "mode": payload.route_mode,
        },
    )

    # ── Cache lookup ──────────────────────────────────────────────────────────
    route_hash = compute_route_hash(
        payload.origin_lat,
        payload.origin_lng,
        payload.dest_lat,
        payload.dest_lng,
        payload.route_mode,
    )
    cached = await get_cached_polyline(db, route_hash)
    cache_hit = cached is not None

    if cache_hit:
        encoded_polyline = cached
        logger.info("Route cache hit", extra={"event": "cache_hit", "hash": route_hash[:8]})
    else:
        # ── Google Routes API ─────────────────────────────────────────────────
        encoded_polyline = await fetch_encoded_polyline(
            origin_lat=payload.origin_lat,
            origin_lng=payload.origin_lng,
            dest_lat=payload.dest_lat,
            dest_lng=payload.dest_lng,
            api_key=settings.google_maps_api_key,
            scenic=(payload.route_mode == RouteMode.scenic),
        )
        await save_route_cache(db, route_hash, encoded_polyline)

    # ── Quickest: no PostGIS query ────────────────────────────────────────────
    if payload.route_mode == RouteMode.quickest:
        return TripPlanResponse(
            route_status="OK",
            injected_waypoints_count=0,
            injected_poi_names=[],
            native_maps_url=build_maps_url(
                payload.origin_lat,
                payload.origin_lng,
                payload.dest_lat,
                payload.dest_lng,
                waypoints=[],
            ),
            waypoints=[],
            cache_hit=cache_hit,
        )

    # ── Scenic: bounding box macro search ────────────────────────────────────
    waypoints = await fetch_scenic_anchor(
        db=db,
        origin_lat=payload.origin_lat,
        origin_lng=payload.origin_lng,
        dest_lat=payload.dest_lat,
        dest_lng=payload.dest_lng,
    )

    logger.info(
        "Trip planned",
        extra={
            "event": "trip_plan_complete",
            "mode": payload.route_mode,
            "waypoints_injected": len(waypoints),
            "cache_hit": cache_hit,
        },
    )

    return TripPlanResponse(
        route_status="OK",
        injected_waypoints_count=len(waypoints),
        injected_poi_names=[wp.name for wp in waypoints],
        native_maps_url=build_maps_url(
            payload.origin_lat,
            payload.origin_lng,
            payload.dest_lat,
            payload.dest_lng,
            waypoints=waypoints,
        ),
        waypoints=waypoints,
        cache_hit=cache_hit,
    )
