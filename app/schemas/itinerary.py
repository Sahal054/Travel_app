from __future__ import annotations
from pydantic import BaseModel
from typing import Literal


class ItineraryRequest(BaseModel):
    destination: str
    budget: Literal["backpacker", "standard", "luxury"] = "standard"
    duration_days: int = 3


class Activity(BaseModel):
    time: str
    period: Literal["morning", "afternoon", "evening", "night"]
    name: str
    type: str
    duration_minutes: int
    description: str
    estimated_cost_inr: int
    rating: float | None = None


class Accommodation(BaseModel):
    name: str
    type: str
    price_per_night_inr: int
    rating: float | None = None
    address: str | None = None


class ItineraryDay(BaseModel):
    day_number: int
    theme: str
    activities: list[Activity]
    accommodation: Accommodation


class ItineraryResponse(BaseModel):
    destination: str
    duration_days: int
    budget_level: str
    days: list[ItineraryDay]
    itinerary_id: int | None = None
