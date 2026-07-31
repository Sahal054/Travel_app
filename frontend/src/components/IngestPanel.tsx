'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ingestReel } from '@/lib/api';
import type { PlaceSummary } from '@/lib/types';

const PLATFORMS: { pattern: RegExp; name: string; color: string }[] = [
  { pattern: /instagram\.com/,          name: 'Instagram', color: 'bg-pink-600' },
  { pattern: /tiktok\.com/,             name: 'TikTok',    color: 'bg-slate-800 border border-slate-600' },
  { pattern: /youtube\.com\/shorts|youtu\.be/, name: 'YouTube Shorts', color: 'bg-red-600' },
];

function detectPlatform(url: string) {
  return PLATFORMS.find((p) => p.pattern.test(url)) ?? null;
}

function confidenceColor(score: number) {
  if (score >= 0.85) return 'text-emerald-400';
  if (score >= 0.65) return 'text-amber-400';
  return 'text-rose-400';
}

function confidenceLabel(score: number) {
  if (score >= 0.85) return 'High confidence';
  if (score >= 0.65) return 'Medium confidence';
  return 'Low confidence';
}

interface HistoryEntry {
  place_name: string;
  country: string | null;
  confidence: number;
  latitude: number;
  longitude: number;
  reel_url: string;
}

interface Props {
  onPlaceExtracted: (place: PlaceSummary) => void;
}

export default function IngestPanel({ onPlaceExtracted }: Props) {
  const router = useRouter();
  const [url, setUrl]         = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);
  const [result, setResult]   = useState<PlaceSummary | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  // Load history from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem('ingest_history');
      if (stored) setHistory(JSON.parse(stored) as HistoryEntry[]);
    } catch {}
  }, []);

  const platform = detectPlatform(url);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim()) return;
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const res = await ingestReel(url.trim());
      if (!res.place_summary) throw new Error(res.message ?? 'No place extracted');
      setResult(res.place_summary);
      onPlaceExtracted(res.place_summary);

      // Prepend to history (max 6 entries)
      const entry: HistoryEntry = {
        place_name:  res.place_summary.place_name,
        country:     res.place_summary.country,
        confidence:  res.place_summary.confidence,
        latitude:    res.place_summary.latitude,
        longitude:   res.place_summary.longitude,
        reel_url:    url.trim(),
      };
      const next = [entry, ...history].slice(0, 6);
      setHistory(next);
      localStorage.setItem('ingest_history', JSON.stringify(next));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }

  return (
    <aside className="absolute left-4 top-16 bottom-4 w-80 z-10 flex flex-col gap-3 overflow-y-auto">
      {/* Header */}
      <div className="rounded-2xl bg-slate-900/80 backdrop-blur-md border border-slate-700/60 p-5 shadow-2xl">
        <p className="text-xs font-semibold text-pink-400 tracking-widest uppercase mb-1">Phase 1</p>
        <h1 className="text-xl font-bold text-white leading-tight">Reel Ingestion</h1>
        <p className="text-xs text-slate-400 mt-1">
          Paste a social media reel URL and the AI pipeline extracts the location.
        </p>
      </div>

      {/* Form */}
      <form
        onSubmit={handleSubmit}
        className="rounded-2xl bg-slate-900/80 backdrop-blur-md border border-slate-700/60 p-5 shadow-2xl flex flex-col gap-4"
      >
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wide">
              Reel URL
            </label>
            {platform && (
              <span className={`text-xs text-white font-medium rounded-full px-2 py-0.5 ${platform.color}`}>
                {platform.name}
              </span>
            )}
          </div>
          <div className="flex gap-2">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://www.instagram.com/reel/…"
              className="flex-1 rounded-lg bg-slate-800 border border-slate-600 text-white text-sm
                         px-3 py-2 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-pink-500"
            />
            <button
              type="button"
              title="Paste from clipboard"
              onClick={async () => {
                const text = await navigator.clipboard.readText().catch(() => '');
                if (text) setUrl(text);
              }}
              className="rounded-lg bg-slate-700 hover:bg-slate-600 px-3 py-2 text-slate-300
                         text-sm transition-colors"
            >
              ⌘V
            </button>
          </div>
        </div>

        <button
          type="submit"
          disabled={!url.trim() || loading}
          className="w-full rounded-xl bg-pink-600 hover:bg-pink-500 disabled:bg-slate-700
                     disabled:text-slate-500 text-white font-semibold py-3 transition-colors"
        >
          {loading ? 'Extracting location…' : 'Extract Location'}
        </button>

        {loading && (
          <div className="flex flex-col items-center gap-2 py-2">
            <div className="h-8 w-8 rounded-full border-2 border-pink-500 border-t-transparent animate-spin" />
            <p className="text-xs text-slate-400 text-center">
              AI pipeline running — this may take up to 30 seconds
            </p>
          </div>
        )}

        {error && (
          <p className="text-xs text-red-400 bg-red-900/30 rounded-lg px-3 py-2 border border-red-800">
            {error}
          </p>
        )}
      </form>

      {/* Result */}
      {result && (
        <div className="rounded-2xl bg-slate-900/80 backdrop-blur-md border border-slate-700/60 p-5 shadow-2xl flex flex-col gap-3">
          <div className="flex items-start justify-between gap-2">
            <h2 className="text-base font-bold text-white leading-snug">{result.place_name}</h2>
            <span className={`text-xs font-semibold shrink-0 ${confidenceColor(result.confidence)}`}>
              {Math.round(result.confidence * 100)}%
            </span>
          </div>

          {result.formatted_address && (
            <p className="text-xs text-slate-400">{result.formatted_address}</p>
          )}

          <div className="flex flex-wrap gap-2 text-xs">
            {result.city    && <Chip>{result.city}</Chip>}
            {result.region  && <Chip>{result.region}</Chip>}
            {result.country && <Chip>{result.country}</Chip>}
          </div>

          <div className="rounded-lg bg-slate-800 px-3 py-2 text-xs text-slate-300 font-mono">
            {result.latitude.toFixed(5)}, {result.longitude.toFixed(5)}
          </div>

          {/* Confidence bar */}
          <div className="flex flex-col gap-1">
            <div className="flex justify-between text-xs text-slate-500">
              <span>{confidenceLabel(result.confidence)}</span>
              <span>{Math.round(result.confidence * 100)}%</span>
            </div>
            <div className="h-1.5 rounded-full bg-slate-700 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  result.confidence >= 0.85 ? 'bg-emerald-500'
                  : result.confidence >= 0.65 ? 'bg-amber-500'
                  : 'bg-rose-500'
                }`}
                style={{ width: `${result.confidence * 100}%` }}
              />
            </div>
          </div>

          <button
            onClick={() =>
              router.push(
                `/?dest_lat=${result.latitude}&dest_lng=${result.longitude}&dest_name=${encodeURIComponent(result.place_name)}`,
              )
            }
            className="w-full rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white
                       font-semibold py-2.5 text-sm transition-colors"
          >
            Plan a Route Here →
          </button>
        </div>
      )}

      {/* History */}
      {history.length > 0 && (
        <div className="rounded-2xl bg-slate-900/80 backdrop-blur-md border border-slate-700/60 p-5 shadow-2xl flex flex-col gap-3">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Recent</p>
          <ul className="flex flex-col gap-2">
            {history.map((h, i) => (
              <li
                key={i}
                onClick={() => onPlaceExtracted({
                  place_name: h.place_name,
                  formatted_address: null,
                  city: null,
                  region: null,
                  country: h.country,
                  latitude: h.latitude,
                  longitude: h.longitude,
                  confidence: h.confidence,
                })}
                className="flex items-center gap-2 cursor-pointer rounded-lg hover:bg-slate-800 px-2 py-1.5 transition-colors"
              >
                <span className="h-2 w-2 rounded-full bg-pink-500 shrink-0" />
                <span className="text-sm text-white truncate flex-1">{h.place_name}</span>
                <span className={`text-xs shrink-0 ${confidenceColor(h.confidence)}`}>
                  {Math.round(h.confidence * 100)}%
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </aside>
  );
}

function Chip({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded-full bg-slate-700 text-slate-300 px-2 py-0.5">{children}</span>
  );
}
