import type {
  TripPlanRequest, TripPlanResponse, IngestReelResponse,
  OptimizeRequest, OptimizedRoute,
  ItineraryRequest, ItineraryResponse,
  RatesRequest, OTARate,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

async function _fetch<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail?: string }).detail ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function planTrip(req: TripPlanRequest): Promise<TripPlanResponse> {
  return _fetch<TripPlanResponse>(`${API_BASE}/api/v1/trips/plan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
}

export async function ingestReel(url: string): Promise<IngestReelResponse> {
  return _fetch<IngestReelResponse>(`${API_BASE}/ingest/reel`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reel_url: url }),
  });
}

export async function optimizeRoute(req: OptimizeRequest): Promise<OptimizedRoute> {
  return _fetch<OptimizedRoute>(`${API_BASE}/api/v1/trips/optimize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
}

export async function generateItinerary(req: ItineraryRequest): Promise<ItineraryResponse> {
  return _fetch<ItineraryResponse>(`${API_BASE}/api/v1/trips/itinerary`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
}

export async function compareRates(req: RatesRequest): Promise<OTARate[]> {
  const params = new URLSearchParams({
    hotel_name: req.hotel_name,
    destination: req.destination,
    ...(req.budget_level && { budget_level: req.budget_level }),
    ...(req.base_price && { base_price: String(req.base_price) }),
  });
  return _fetch<OTARate[]>(`${API_BASE}/api/v1/rates/compare?${params.toString()}`);
}
