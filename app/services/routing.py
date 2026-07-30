import logging
from urllib.parse import urlencode
from typing import List

import httpx
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.trips import InjectedWaypoint

logger = logging.getLogger(__name__)

GOOGLE_ROUTES_API_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"


async def fetch_encoded_polyline(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    api_key: str,
) -> str:
    """Call Google Routes API v2 and return the encoded polyline string."""

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "routes.polyline.encodedPolyline",
    }

    body = {
        "origin": {
            "location": {
                "latLng": {"latitude": origin_lat, "longitude": origin_lng}
            }
        },
        "destination": {
            "location": {
                "latLng": {"latitude": dest_lat, "longitude": dest_lng}
            }
        },
        "travelMode": "DRIVE",
        "routingPreference": "TRAFFIC_AWARE",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                GOOGLE_ROUTES_API_URL, json=body, headers=headers
            )
            response.raise_for_status()
    except httpx.TimeoutException:
        logger.error("Google Routes API timed out")
        raise HTTPException(status_code=504, detail="Google Routes API timed out.")
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Google Routes API HTTP error",
            extra={"status_code": exc.response.status_code},
        )
        raise HTTPException(
            status_code=502,
            detail=f"Google Routes API returned {exc.response.status_code}: {exc.response.text}",
        )
    except httpx.RequestError as exc:
        logger.error("Google Routes API request error", extra={"error": str(exc)})
        raise HTTPException(
            status_code=502,
            detail=f"Failed to reach Google Routes API: {str(exc)}",
        )

    data = response.json()

    try:
        encoded_polyline: str = data["routes"][0]["polyline"]["encodedPolyline"]
    except (KeyError, IndexError):
        raise HTTPException(
            status_code=502,
            detail="Google Routes API returned an unexpected response structure.",
        )

    return encoded_polyline


async def fetch_pois_along_route(
    db: AsyncSession,
    encoded_polyline: str,
    search_radius_meters: int,
    poi_type: str,
    limit: int = 2,
) -> List[InjectedWaypoint]:
    """
    Query PostGIS to find POIs within search_radius_meters of the decoded polyline.

    - ST_LineFromEncodedPolyline decodes the Google polyline natively in the DB.
    - The result is cast to Geography so ST_DWithin accepts meters directly,
      matching the Geography type used by the places.location column.
    - place_types is a TEXT[] column; the ANY operator checks membership.
    - Results are ordered by proximity to the route line and capped at `limit`.
    """

    sql = text(
        """
        SELECT
            p.place_name,
            p.place_types,
            ST_Y(p.location::geometry)  AS lat,
            ST_X(p.location::geometry)  AS lng
        FROM places p
        WHERE
            :poi_type = ANY(p.place_types)
            AND ST_DWithin(
                p.location,
                ST_LineFromEncodedPolyline(:encoded_polyline)::geography,
                :radius
            )
        ORDER BY
            ST_Distance(
                p.location,
                ST_LineFromEncodedPolyline(:encoded_polyline)::geography
            )
        LIMIT :limit
        """
    )

    try:
        result = await db.execute(
            sql,
            {
                "poi_type": poi_type,
                "encoded_polyline": encoded_polyline,
                "radius": search_radius_meters,
                "limit": limit,
            },
        )
        rows = result.fetchall()
    except Exception as exc:
        logger.error("PostGIS route query failed", extra={"error": str(exc)})
        raise HTTPException(status_code=503, detail=f"Database query failed: {str(exc)}")

    return [
        InjectedWaypoint(
            name=row.place_name,
            lat=float(row.lat),
            lng=float(row.lng),
            poi_type=poi_type,
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
