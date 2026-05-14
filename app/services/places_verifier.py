from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings
from app.services.gemini_location_extractor import LocationCandidate


@dataclass(frozen=True)
class VerifiedPlace:
    google_place_id: str
    place_name: str
    formatted_address: str | None
    city: str | None
    region: str | None
    country: str | None
    latitude: float
    longitude: float
    score: float


@dataclass(frozen=True)
class PlaceVerificationResult:
    success: bool
    place: VerifiedPlace | None
    error: str | None


class GooglePlacesVerifier:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        region: str | None = "in",
        language: str | None = "en",
        timeout_seconds: float = 10.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = api_key or settings.google_maps_api_key
        if not self.api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY is not configured")

        self.region = region
        self.language = language
        self.timeout = timeout_seconds
        self.client = client

    async def resolve_best(
        self, candidates: list[LocationCandidate]
    ) -> PlaceVerificationResult:
        if not candidates:
            return PlaceVerificationResult(
                success=False,
                place=None,
                error="No candidates provided",
            )

        best: VerifiedPlace | None = None
        
        # FIX: Efficient connection reuse across sequential loop entries
        client_to_use = self.client or httpx.AsyncClient(timeout=self.timeout)
        
        try:
            for candidate in candidates:
                query = self._build_query(candidate)
                places = await self._find_places(client_to_use, query, candidate)

                for place in places:
                    # In the New API, Text Search returns complete nested fields.
                    # We can pass the place dict right to details parsing,
                    # removing redundant Details API HTTP requests.
                    verified = self._to_verified_place(candidate, place)

                    if best is None or verified.score > best.score:
                        best = verified
        finally:
            if self.client is None:
                await client_to_use.aclose()

        if not best:
            return PlaceVerificationResult(
                success=False,
                place=None,
                error="No Places results matched candidates",
            )

        return PlaceVerificationResult(success=True, place=best, error=None)

    def _build_query(self, candidate: LocationCandidate) -> str:
        parts = [
            candidate.place_name,
            candidate.city,
            candidate.region,
            candidate.country,
        ]
        cleaned = [part.strip() for part in parts if part and part.strip()]
        return ", ".join(cleaned)

    async def _find_places(
        self,
        client: httpx.AsyncClient,
        query: str,
        candidate: LocationCandidate,
    ) -> list[dict[str, Any]]:
        # UPGRADE: New Unified Text Search endpoint 
        url = "https://places.googleapis.com/v1/places:searchText"
        
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            # COST SAVING: Field masks limit payload attributes to prevent pricing overheads
            "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.addressComponents"
        }

        body: dict[str, Any] = {"textQuery": query}

        if self.language:
            body["languageCode"] = self.language
        if self.region:
            body["regionCode"] = self.region
            
        # UPGRADE: Structured location bias format for the New API
        if candidate.latitude is not None and candidate.longitude is not None:
            body["locationBias"] = {
                "circle": {
                    "center": {
                        "latitude": candidate.latitude,
                        "longitude": candidate.longitude
                    },
                    "radius": 50000.0  # 50km radius
                }
            }

        resp = await client.post(url, json=body, headers=headers)
        
        if resp.status_code != 200:
            return []
            
        data = resp.json()
        return data.get("places", [])

    def _to_verified_place(
        self,
        candidate: LocationCandidate,
        place: dict[str, Any],
    ) -> VerifiedPlace:
        # UPGRADE: Parsing raw camelCase geolocation objects
        location = place.get("location") or {}
        lat = location.get("latitude")
        lng = location.get("longitude")

        # UPGRADE: Map camelCase fields for structured addresses
        city, region, country = self._parse_address_components(
            place.get("addressComponents", [])
        )

        # UPGRADE: Target localized displayName strings safely
        display_name_obj = place.get("displayName") or {}
        place_name = display_name_obj.get("text") or candidate.place_name
        formatted_address = place.get("formattedAddress")

        score = self._score_match(
            candidate=candidate,
            place_name=place_name,
            city=city,
            region=region,
            country=country,
            lat=lat,
            lng=lng,
        )

        return VerifiedPlace(
            google_place_id=place["id"],
            place_name=place_name,
            formatted_address=formatted_address,
            city=city,
            region=region,
            country=country,
            latitude=lat or 0.0,
            longitude=lng or 0.0,
            score=score,
        )

    @staticmethod
    def _parse_address_components(components: list[dict[str, Any]]) -> tuple[
        str | None, str | None, str | None
    ]:
        city = region = country = None

        def _name(comp: dict[str, Any]) -> str | None:
            return comp.get("longText") or comp.get("shortText")

        for comp in components:
            types = comp.get("types", [])
            if "locality" in types and not city:
                city = _name(comp)
            if "administrative_area_level_1" in types and not region:
                region = _name(comp)
            if "country" in types and not country:
                country = _name(comp)

        if not city:
            for comp in components:
                if "administrative_area_level_2" in comp.get("types", []):
                    city = _name(comp)
                    break

        return city, region, country

    def _score_match(
        self,
        *,
        candidate: LocationCandidate,
        place_name: str,
        city: str | None,
        region: str | None,
        country: str | None,
        lat: float | None,
        lng: float | None,
    ) -> float:
        score = candidate.confidence if candidate.confidence is not None else 0.3

        if city and candidate.city and city.lower() == candidate.city.lower():
            score += 0.2
        if region and candidate.region and region.lower() == candidate.region.lower():
            score += 0.15
        if country and candidate.country and country.lower() == candidate.country.lower():
            score += 0.1

        if candidate.place_name and place_name:
            if candidate.place_name.lower() in place_name.lower():
                score += 0.1

        if (
            candidate.latitude is not None
            and candidate.longitude is not None
            and lat is not None
            and lng is not None
        ):
            distance_km = self._haversine_km(
                candidate.latitude, candidate.longitude, lat, lng
            )
            score -= min(distance_km / 200.0, 1.0) * 0.25

        return max(0.0, min(score, 1.0))

    @staticmethod
    def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return r * c
