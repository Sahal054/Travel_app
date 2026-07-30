import hashlib
import logging
from urllib.parse import urlencode
from typing import List, Optional

import httpx
from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.route_cache import RouteCache
from app.schemas.trips import InjectedWaypoint, RouteMode

logger = logging.getLogger(__name__)

GOOGLE_ROUTES_API_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
# Bounding box padding in degrees to capture POIs on curved routes (~11 km per side)
BBOX_EXPAND_DEG = 0.1


def compute_route_hash(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    mode: RouteMode,
) -> str:
    """Snap coords to ~100 m grid (3 dp) and SHA-256 hash with the route mode."""
    key = (
        f"{round(origin_lat, 3)},"
        f"{round(origin_lng, 3)},"
        f"{round(dest_lat, 3)},"
        f"{round(dest_lng, 3)},"
        f"{mode.value}"
    )
    return hashlib.sha256(key.encode()).hexdigest()


async def get_cached_polyline(db: AsyncSession, route_hash: str) -> Optional[str]:
    """Return cached polyline for this hash, or None on a miss."""
    result = await db.execute(
        select(RouteCache.encoded_polyline).where(RouteCache.route_hash == route_hash)
    )
    return result.scalar_one_or_none()


async def save_route_cache(
    db: AsyncSession, route_hash: str, encoded_polyline: str
) -> None:
    """Insert into route_cache; silently skip on duplicate hash (race-safe)."""
    stmt = (
        pg_insert(RouteCache)
        .values(route_hash=route_hash, encoded_polyline=encoded_polyline)
        .on_conflict_do_nothing(index_elements=["route_hash"])
    )
    try:
        await db.execute(stmt)
        await db.commit()
    except Exception as exc:
        logger.warning("Route cache write failed (non-fatal)", extra={"error": str(exc)})
        await db.rollback()


async def fetch_encoded_polyline(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    api_key: str,
    scenic: bool = False,
) -> str:
    """Call Google Routes API v2 and return the encoded polyline string."""
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "routes.polyline.encodedPolyline",
    }
    body = {
        "origin": {"location": {"latLng": {"latitude": origin_lat, "longitude": origin_lng}}},
        "destination": {"location": {"latLng": {"latitude": dest_lat, "longitude": dest_lng}}},
        "travelMode": "DRIVE",
        "routingPreference": "TRAFFIC_AWARE",
    }
    if scenic:
        body["routeModifiers"] = {"avoidHighways": True}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(GOOGLE_ROUTES_API_URL, json=body, headers=headers)
            response.raise_for_status()
    except httpx.TimeoutException:
        logger.error("Google Routes API timed out")
        raise HTTPException(status_code=504, detail="Google Routes API timed out.")
    except httpx.HTTPStatusError as exc:
        logger.error("Google Routes API HTTP error", extra={"status_code": exc.response.status_code})
        raise HTTPException(
            status_code=502,
            detail=f"Google Routes API returned {exc.response.status_code}: {exc.response.text}",
        )
    except httpx.RequestError as exc:
        logger.error("Google Routes API request error", extra={"error": str(exc)})
        raise HTTPException(status_code=502, detail=f"Failed to reach Google Routes API: {str(exc)}")

    try:
        return response.json()["routes"][0]["polyline"]["encodedPolyline"]
    except (KeyError, IndexError):
        raise HTTPException(status_code=502, detail="Google Routes API returned unexpected structure.")


async def fetch_scenic_anchor(
    db: AsyncSession,
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
) -> List[InjectedWaypoint]:
    """
    PostGIS bounding box macro search for a single scenic anchor POI.

    ST_MakeEnvelope builds a box from origin/dest corners (EPSG:4326).
    ST_Expand pads the box by BBOX_EXPAND_DEG degrees on each side to capture
    POIs on routes that curve outside the straight-line bounding box.
    The && array overlap operator matches any scenic place_type.
    Results ordered by ST_Distance to ST_Centroid of the envelope, limit 1.
    """
    sql = text(
        """
        SELECT
            p.place_name,
            p.place_types,
            ST_Y(p.location::geometry) AS lat,
            ST_X(p.location::geometry) AS lng
        FROM places p
        WHERE
            p.place_types && ARRAY['scenic_viewpoint', 'scenic_road', 'tourist_attraction']::varchar[]
            AND ST_Within(
                p.location::geometry,
                ST_Expand(
                    ST_MakeEnvelope(:min_lng, :min_lat, :max_lng, :max_lat, 4326),
                    :expand_deg
                )
            )
        ORDER BY
            ST_Distance(
                p.location::geometry,
                ST_Centroid(ST_MakeEnvelope(:min_lng, :min_lat, :max_lng, :max_lat, 4326))
            )
        LIMIT 1
        """
    )
    try:
        result = await db.execute(
            sql,
            {
                "min_lng": min(origin_lng, dest_lng),
                "min_lat": min(origin_lat, dest_lat),
                "max_lng": max(origin_lng, dest_lng),
                "max_lat": max(origin_lat, dest_lat),
                "expand_deg": BBOX_EXPAND_DEG,
            },
        )
        rows = result.fetchall()
    except Exception as exc:
        logger.error("PostGIS scenic anchor query failed", extra={"error": str(exc)})
        raise HTTPException(status_code=503, detail=f"Database query failed: {str(exc)}")

    return [
        InjectedWaypoint(
            name=row.place_name,
            lat=float(row.lat),
            lng=float(row.lng),
            poi_type=row.place_types[0] if row.place_types else "scenic",
        )
        for row in rows
    ]


def build_maps_url(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    waypoints: List[InjectedWaypoint],
) -> str:
    """Compile a Google Maps Universal deep link URL."""
    params: dict = {
        "api": "1",
        "origin": f"{origin_lat},{origin_lng}",
        "destination": f"{dest_lat},{dest_lng}",
        "travelmode": "driving",
    }
    if waypoints:
        params["waypoints"] = "|".join(f"{wp.lat},{wp.lng}" for wp in waypoints)
    return f"https://www.google.com/maps/dir/?{urlencode(params)}"
