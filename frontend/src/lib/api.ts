import type { TripPlanRequest, TripPlanResponse, IngestReelResponse } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export async function planTrip(req: TripPlanRequest): Promise<TripPlanResponse> {
  const res = await fetch(`${API_BASE}/api/v1/trips/plan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail?: string }).detail ?? 'Failed to plan trip');
  }
  return res.json() as Promise<TripPlanResponse>;
}

export async function ingestReel(url: string): Promise<IngestReelResponse> {
  const res = await fetch(`${API_BASE}/ingest/reel`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reel_url: url }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error((err as { detail?: string }).detail ?? 'Ingestion failed');
  }
  return res.json() as Promise<IngestReelResponse>;
}
