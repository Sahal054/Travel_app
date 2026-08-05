from __future__ import annotations

import asyncio
import json
import logging

from google import genai
from google.genai import types

from app.core.config import settings
from app.schemas.itinerary import ItineraryResponse

logger = logging.getLogger(__name__)

_BUDGET_HINTS = {
    "backpacker": "hostels, street food, budget guesthouses under ₹1000/night, public transport",
    "standard":   "3-star hotels, sit-down restaurants, mix of local and tourist-grade venues, under ₹4000/night",
    "luxury":     "5-star resorts, fine-dining, private transfers, spa treatments, ₹8000+/night",
}

_SYSTEM_PROMPT = """You are an expert Indian travel planner.
Return ONLY a valid JSON object matching this exact schema — no markdown, no commentary:
{
  "destination": string,
  "duration_days": integer,
  "budget_level": string,
  "days": [
    {
      "day_number": integer,
      "theme": string,
      "activities": [
        {
          "time": "HH:MM",
          "period": "morning"|"afternoon"|"evening"|"night",
          "name": string,
          "type": string,
          "duration_minutes": integer,
          "description": string,
          "estimated_cost_inr": integer,
          "rating": float|null
        }
      ],
      "accommodation": {
        "name": string,
        "type": string,
        "price_per_night_inr": integer,
        "rating": float|null,
        "address": string|null
      }
    }
  ]
}
Include 4-5 activities per day covering morning, afternoon, evening and optionally night.
Focus on real, well-known venues with accurate names. Include late-night food spots, local
restaurants (Mandi/Arabian/seafood/pizza as relevant to the destination), and beachside/
scenic stays."""


class ItineraryService:
    def __init__(self, api_key: str | None = None) -> None:
        key = api_key or settings.gemini_api_key
        if not key:
            raise ValueError("GEMINI_API_KEY is not configured")
        self.client = genai.Client(api_key=key)

    async def generate(
        self,
        destination: str,
        budget: str,
        duration_days: int,
    ) -> ItineraryResponse:
        return await asyncio.to_thread(self._generate_sync, destination, budget, duration_days)

    def _generate_sync(
        self,
        destination: str,
        budget: str,
        duration_days: int,
    ) -> ItineraryResponse:
        budget_hint = _BUDGET_HINTS.get(budget, _BUDGET_HINTS["standard"])
        user_prompt = (
            f"Generate a {duration_days}-day {budget} itinerary for {destination}, India.\n"
            f"Budget context: {budget_hint}."
        )

        response = self.client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=[_SYSTEM_PROMPT, user_prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.7,
            ),
        )
        raw = response.text
        data = json.loads(raw)
        return ItineraryResponse(**data)
