'use client';

import { useState, useEffect } from 'react';
import type { TripPlanRequest, TripPlanResponse, RouteMode } from '@/lib/types';
import { planTrip } from '@/lib/api';

interface Props {
  onTripPlanned: (result: TripPlanResponse) => void;
  onCoordinatesChange: (
    origin: [number, number] | null,
    dest: [number, number] | null,
  ) => void;
  initialDestLat?: number;
  initialDestLng?: number;
  initialDestName?: string;
}

interface CoordField {
  lat: string;
  lng: string;
}

const EMPTY: CoordField = { lat: '', lng: '' };

export default function TripPlannerPanel({ onTripPlanned, onCoordinatesChange, initialDestLat, initialDestLng, initialDestName }: Props) {
  const [origin, setOrigin] = useState<CoordField>(EMPTY);
  const [dest, setDest]     = useState<CoordField>(
    initialDestLat != null && initialDestLng != null
      ? { lat: initialDestLat.toFixed(6), lng: initialDestLng.toFixed(6) }
      : EMPTY,
  );
  const [mode, setMode]     = useState<RouteMode>('scenic');

  // Notify parent map of pre-filled destination pin on first render
  useEffect(() => {
    if (initialDestLat != null && initialDestLng != null) {
      onCoordinatesChange(null, [initialDestLng, initialDestLat]);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState<string | null>(null);
  const [result, setResult]     = useState<TripPlanResponse | null>(null);

  function notifyParent(o: CoordField, d: CoordField) {
    const originPair  = o.lat && o.lng ? ([parseFloat(o.lng), parseFloat(o.lat)] as [number, number]) : null;
    const destPair    = d.lat && d.lng ? ([parseFloat(d.lng), parseFloat(d.lat)] as [number, number]) : null;
    onCoordinatesChange(originPair, destPair);
  }

  function handleOriginChange(field: keyof CoordField, val: string) {
    const next = { ...origin, [field]: val };
    setOrigin(next);
    notifyParent(next, dest);
  }

  function handleDestChange(field: keyof CoordField, val: string) {
    const next = { ...dest, [field]: val };
    setDest(next);
    notifyParent(origin, next);
  }

  async function useMyLocation() {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition((pos) => {
      const next = {
        lat: pos.coords.latitude.toFixed(6),
        lng: pos.coords.longitude.toFixed(6),
      };
      setOrigin(next);
      notifyParent(next, dest);
    });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const req: TripPlanRequest = {
        origin_lat: parseFloat(origin.lat),
        origin_lng: parseFloat(origin.lng),
        dest_lat:   parseFloat(dest.lat),
        dest_lng:   parseFloat(dest.lng),
        route_mode: mode,
      };
      const res = await planTrip(req);
      setResult(res);
      onTripPlanned(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }

  const canSubmit =
    origin.lat && origin.lng && dest.lat && dest.lng && !loading;

  return (
    <aside className="absolute left-4 top-20 bottom-4 w-80 z-10 flex flex-col gap-3 overflow-y-auto">
      {/* Header card */}
      <div className="rounded-2xl bg-slate-900/80 backdrop-blur-md border border-slate-700/60 p-5 shadow-2xl">
        <p className="text-xs font-semibold text-emerald-400 tracking-widest uppercase mb-1">
          Route Planner
        </p>
        <h1 className="text-2xl font-bold text-white leading-tight">
          Travelling<br />Salesman
        </h1>
      </div>

      {/* Form card */}
      <form
        onSubmit={handleSubmit}
        className="rounded-2xl bg-slate-900/80 backdrop-blur-md border border-slate-700/60 p-5 shadow-2xl flex flex-col gap-4"
      >
        {/* Origin */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wide">
              Origin
            </label>
            <button
              type="button"
              onClick={useMyLocation}
              className="text-xs text-emerald-400 hover:text-emerald-300 transition-colors"
            >
              Use my location
            </button>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <input
              type="number"
              step="any"
              placeholder="Latitude"
              value={origin.lat}
              onChange={(e) => handleOriginChange('lat', e.target.value)}
              className="rounded-lg bg-slate-800 border border-slate-600 text-white text-sm px-3 py-2
                         placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
            <input
              type="number"
              step="any"
              placeholder="Longitude"
              value={origin.lng}
              onChange={(e) => handleOriginChange('lng', e.target.value)}
              className="rounded-lg bg-slate-800 border border-slate-600 text-white text-sm px-3 py-2
                         placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>
        </div>

        {/* Destination */}
        <div className="flex flex-col gap-2">
          <label className="text-xs font-semibold text-slate-400 uppercase tracking-wide">
            Destination
          </label>
          {initialDestName && (
            <p className="text-xs text-emerald-400 bg-emerald-950/50 rounded-lg px-3 py-1.5 border border-emerald-800/40">
              📍 From reel: {initialDestName}
            </p>
          )}
          <div className="grid grid-cols-2 gap-2">
            <input
              type="number"
              step="any"
              placeholder="Latitude"
              value={dest.lat}
              onChange={(e) => handleDestChange('lat', e.target.value)}
              className="rounded-lg bg-slate-800 border border-slate-600 text-white text-sm px-3 py-2
                         placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
            <input
              type="number"
              step="any"
              placeholder="Longitude"
              value={dest.lng}
              onChange={(e) => handleDestChange('lng', e.target.value)}
              className="rounded-lg bg-slate-800 border border-slate-600 text-white text-sm px-3 py-2
                         placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>
        </div>

        {/* Route Mode */}
        <div className="flex flex-col gap-2">
          <label className="text-xs font-semibold text-slate-400 uppercase tracking-wide">
            Route Mode
          </label>
          <div className="flex rounded-lg bg-slate-800 border border-slate-600 p-1">
            {(['scenic', 'quickest'] as const).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => setMode(m)}
                className={`flex-1 rounded-md py-1.5 text-sm font-medium transition-all ${
                  mode === m
                    ? 'bg-emerald-600 text-white shadow'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {m.charAt(0).toUpperCase() + m.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={!canSubmit}
          className="w-full rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700
                     disabled:text-slate-500 text-white font-semibold py-3 transition-colors"
        >
          {loading ? 'Planning…' : 'Plan My Route'}
        </button>

        {error && (
          <p className="text-xs text-red-400 bg-red-900/30 rounded-lg px-3 py-2 border border-red-800">
            {error}
          </p>
        )}
      </form>

      {/* Results card */}
      {result && (
        <div className="rounded-2xl bg-slate-900/80 backdrop-blur-md border border-slate-700/60 p-5 shadow-2xl flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Result</span>
            {result.cache_hit && (
              <span className="text-xs bg-slate-700 text-slate-300 rounded-full px-2 py-0.5">
                Cached
              </span>
            )}
          </div>

          {result.injected_waypoints_count === 0 ? (
            <p className="text-sm text-slate-400">No scenic POIs found along this route.</p>
          ) : (
            <ul className="flex flex-col gap-1.5">
              {result.waypoints.map((wp, i) => (
                <li key={i} className="flex items-center gap-2 text-sm text-white">
                  <span className="h-2 w-2 rounded-full bg-emerald-500 flex-shrink-0" />
                  <span>{wp.name}</span>
                  <span className="ml-auto text-xs text-slate-500">{wp.poi_type}</span>
                </li>
              ))}
            </ul>
          )}

          <a
            href={result.native_maps_url}
            target="_blank"
            rel="noopener noreferrer"
            className="w-full text-center rounded-xl bg-blue-600 hover:bg-blue-500 text-white
                       font-semibold py-2.5 text-sm transition-colors"
          >
            Open in Google Maps →
          </a>
        </div>
      )}
    </aside>
  );
}
