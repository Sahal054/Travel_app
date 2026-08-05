import logging
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.schemas.optimize import OptimizeRequest, OptimizedRoute, WaypointInput

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/trips", tags=["trips"])

GOOGLE_ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"


@router.post("/optimize", response_model=OptimizedRoute)
async def optimize_route(payload: OptimizeRequest) -> OptimizedRoute:
    """TSP: reorder waypoints for minimum travel using Google Routes optimizeWaypointOrder."""
    if not settings.google_maps_api_key:
        raise HTTPException(status_code=503, detail="GOOGLE_MAPS_API_KEY not configured")
    if len(payload.waypoints) < 2:
        raise HTTPException(status_code=422, detail="Provide at least 2 waypoints to optimize")

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": settings.google_maps_api_key,
        "X-Goog-FieldMask": (
            "routes.optimizedIntermediateWaypointIndex,"
            "routes.polyline.encodedPolyline"
        ),
    }
    body = {
        "origin": {"location": {"latLng": {
            "latitude": payload.origin_lat,
            "longitude": payload.origin_lng,
        }}},
        "destination": {"location": {"latLng": {
            "latitude": payload.waypoints[-1].lat,
            "longitude": payload.waypoints[-1].lng,
        }}},
        "intermediates": [
            {"location": {"latLng": {"latitude": wp.lat, "longitude": wp.lng}}}
            for wp in payload.waypoints[:-1]
        ],
        "travelMode": "DRIVE",
        "optimizeWaypointOrder": True,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(GOOGLE_ROUTES_URL, json=body, headers=headers)
            res.raise_for_status()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Google Routes API timed out")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Google Routes API error: {exc.response.text}")

    data = res.json()
    try:
        route = data["routes"][0]
        optimized_indices: list[int] = route.get("optimizedIntermediateWaypointIndex", [])
        polyline = route["polyline"]["encodedPolyline"]
    except (KeyError, IndexError):
        raise HTTPException(status_code=502, detail="Unexpected Google Routes response")

    # Rebuild ordered waypoints: intermediates in optimized order, then final destination
    intermediates = payload.waypoints[:-1]
    ordered = [intermediates[i] for i in optimized_indices] + [payload.waypoints[-1]]

    params = {
        "api": "1",
        "origin": f"{payload.origin_lat},{payload.origin_lng}",
        "destination": f"{ordered[-1].lat},{ordered[-1].lng}",
        "travelmode": "driving",
        "waypoints": "|".join(f"{wp.lat},{wp.lng}" for wp in ordered[:-1]),
    }
    maps_url = f"https://www.google.com/maps/dir/?{urlencode(params)}"

    return OptimizedRoute(
        optimized_order=optimized_indices,
        ordered_waypoints=ordered,
        encoded_polyline=polyline,
        native_maps_url=maps_url,
    )
