from __future__ import annotations 


import math
from dataclasses import dataclass
from typing import Any

import httpx




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

