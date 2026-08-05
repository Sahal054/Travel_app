"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import type { ItineraryResponse, ItineraryDay, OTARate } from "@/lib/types";
import { generateItinerary, compareRates } from "@/lib/api";

type Budget = "backpacker" | "standard" | "luxury";

const BUDGET_OPTIONS: { value: Budget; icon: string; label: string; sub: string; color: string; ring: string }[] = [
  { value: "backpacker", icon: "🎒", label: "Backpacker", sub: "Hostels & street food", color: "from-emerald-600/20 to-emerald-500/5", ring: "border-emerald-500" },
  { value: "standard",   icon: "🏨", label: "Standard",   sub: "3-star comfort",        color: "from-sky-600/20 to-sky-500/5",     ring: "border-sky-400" },
  { value: "luxury",     icon: "✨", label: "Luxury",     sub: "5-star resorts",        color: "from-amber-600/20 to-amber-500/5", ring: "border-amber-400" },
];

const PERIOD_STYLE: Record<string, { bg: string; dot: string; label: string }> = {
  morning:   { bg: "bg-amber-500/10 border-amber-500/20",   dot: "bg-amber-400",   label: "Morning" },
  afternoon: { bg: "bg-sky-500/10 border-sky-500/20",       dot: "bg-sky-400",     label: "Afternoon" },
  evening:   { bg: "bg-violet-500/10 border-violet-500/20", dot: "bg-violet-400",  label: "Evening" },
  night:     { bg: "bg-slate-600/20 border-slate-600/30",   dot: "bg-slate-400",   label: "Night" },
};

const ACTIVITY_ICONS: Record<string, string> = {
  beach: "🏖️", temple: "🕌", food: "🍽️", restaurant: "🍽️", cafe: "☕",
  market: "🛍️", hike: "🥾", viewpoint: "🔭", museum: "🏛️", yoga: "🧘",
  lighthouse: "🗼", waterfall: "💧", boat: "⛵", spa: "💆", nightlife: "🌃",
  shopping: "🛍️", lake: "🏞️", park: "🌿", monument: "🗿",
};
function activityIcon(type: string): string {
  const key = type.toLowerCase();
  return Object.entries(ACTIVITY_ICONS).find(([k]) => key.includes(k))?.[1] ?? "📍";
}

const PROVIDER_COLOR: Record<string, string> = {
  agoda: "bg-blue-600", booking: "bg-sky-500",
  expedia: "bg-yellow-500 text-black", makemytrip: "bg-red-600", goibibo: "bg-cyan-600",
};

function RateCard({ rate }: { rate: OTARate }) {
  return (
    <a href={rate.deep_link} target="_blank" rel="noopener noreferrer"
      className={`group relative flex flex-col gap-2 p-4 rounded-2xl border transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg ${
        rate.is_best_deal
          ? "bg-gradient-to-br from-emerald-900/40 to-slate-900 border-emerald-500/40 shadow-emerald-900/20 shadow-md"
          : "bg-slate-900/60 border-slate-700/60 hover:border-slate-600"
      }`}
    >
      {rate.is_best_deal && (
        <span className="absolute -top-2.5 left-4 text-[10px] font-bold bg-emerald-500 text-white px-2 py-0.5 rounded-full shadow">
          BEST DEAL
        </span>
      )}
      {rate.badge && !rate.is_best_deal && (
        <span className="absolute -top-2.5 left-4 text-[10px] font-bold bg-violet-600 text-white px-2 py-0.5 rounded-full shadow">
          {rate.badge.toUpperCase()}
        </span>
      )}
      <div className="flex items-center gap-2">
        <span className={`text-[11px] font-extrabold text-white px-2 py-0.5 rounded-lg ${PROVIDER_COLOR[rate.logo_slug] ?? "bg-slate-700"}`}>
          {rate.provider.slice(0,3).toUpperCase()}
        </span>
        <span className="text-sm font-medium text-slate-200">{rate.provider}</span>
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-xl font-extrabold text-white">₹{rate.price_per_night_inr.toLocaleString("en-IN")}</span>
        <span className="text-xs text-slate-500">/night</span>
      </div>
      {rate.rating != null && (
        <div className="flex items-center gap-1">
          <span className="text-amber-400 text-xs">★</span>
          <span className="text-xs text-slate-400">{rate.rating} · {rate.review_count?.toLocaleString()} reviews</span>
        </div>
      )}
      <span className="text-xs font-medium text-emerald-400 group-hover:text-emerald-300 transition-colors">
        Book on {rate.provider} →
      </span>
    </a>
  );
}

function ActivityCard({ act }: { act: ItineraryDay["activities"][0] }) {
  const style = PERIOD_STYLE[act.period] ?? PERIOD_STYLE.evening;
  return (
    <div className={`rounded-2xl border p-4 ${style.bg} transition-all`}>
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2.5">
          <span className="text-2xl leading-none">{activityIcon(act.type)}</span>
          <div>
            <p className="text-sm font-semibold text-white leading-tight">{act.name}</p>
            <p className="text-xs text-slate-500 capitalize">{act.type}</p>
          </div>
        </div>
        <div className="flex flex-col items-end shrink-0 gap-1">
          <span className="text-xs font-mono text-slate-400">{act.time}</span>
          {act.rating != null && (
            <span className="text-xs text-amber-400">★ {act.rating}</span>
          )}
        </div>
      </div>
      <p className="text-xs text-slate-400 leading-relaxed mb-2">{act.description}</p>
      <div className="flex gap-3 text-[11px]">
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-white/80 ${style.bg}`}>
          <span className={`h-1.5 w-1.5 rounded-full ${style.dot}`} />
          {style.label}
        </span>
        <span className="text-slate-500">{act.duration_minutes} min</span>
        {act.estimated_cost_inr > 0 && (
          <span className="text-slate-500">₹{act.estimated_cost_inr.toLocaleString("en-IN")}</span>
        )}
      </div>
    </div>
  );
}

function DayView({ day, rates, loadingRates }: { day: ItineraryDay; rates: OTARate[]; loadingRates: boolean }) {
  return (
    <div className="space-y-6">
      {/* Theme badge */}
      <div className="inline-flex items-center gap-2 bg-slate-800 rounded-full px-4 py-1.5">
        <span className="h-1.5 w-1.5 rounded-full bg-violet-400" />
        <span className="text-sm text-slate-300">{day.theme}</span>
      </div>

      {/* Activities */}
      <div>
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">Activities</p>
        <div className="flex flex-col gap-3">
          {day.activities.map((act, i) => <ActivityCard key={i} act={act} />)}
        </div>
      </div>

      {/* Accommodation */}
      <div>
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">Where you stay</p>
        <div className="rounded-2xl bg-gradient-to-br from-slate-800/80 to-slate-900 border border-slate-700/60 p-5">
          <div className="flex justify-between items-start gap-3">
            <div className="flex items-start gap-3">
              <span className="text-3xl leading-none mt-0.5">🏨</span>
              <div>
                <p className="font-semibold text-white">{day.accommodation.name}</p>
                <p className="text-xs text-slate-500 capitalize">{day.accommodation.type}</p>
                {day.accommodation.address && (
                  <p className="text-xs text-slate-500 mt-1">{day.accommodation.address}</p>
                )}
              </div>
            </div>
            <div className="text-right shrink-0">
              <p className="text-lg font-extrabold text-white">
                ₹{day.accommodation.price_per_night_inr.toLocaleString("en-IN")}
              </p>
              <p className="text-[10px] text-slate-500">per night</p>
              {day.accommodation.rating != null && (
                <p className="text-xs text-amber-400 mt-0.5">★ {day.accommodation.rating}</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Rates */}
      <div>
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">Compare rates</p>
        {loadingRates ? (
          <div className="flex items-center gap-2 text-sm text-slate-500 py-4">
            <span className="h-4 w-4 rounded-full border-2 border-slate-600 border-t-violet-500 animate-spin" />
            Fetching live rates…
          </div>
        ) : rates.length > 0 ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mt-1">
            {rates.map((r) => <RateCard key={r.provider} rate={r} />)}
          </div>
        ) : (
          <p className="text-sm text-slate-600 italic">Rates unavailable</p>
        )}
      </div>
    </div>
  );
}

export default function ItineraryPanel() {
  const searchParams = useSearchParams();
  const prefilled = searchParams.get("destination") ?? "";

  const [destination, setDestination] = useState(prefilled);
  const [budget, setBudget] = useState<Budget>("standard");
  const [days, setDays] = useState(3);
  const [loading, setLoading] = useState(false);
  const [itinerary, setItinerary] = useState<ItineraryResponse | null>(null);
  const [activeDay, setActiveDay] = useState(0);
  const [rates, setRates] = useState<OTARate[]>([]);
  const [loadingRates, setLoadingRates] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Auto-generate when arriving from ingest with ?destination=
  useEffect(() => {
    if (prefilled && prefilled !== destination) setDestination(prefilled);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prefilled]);

  async function fetchRates(hotelName: string, dest: string, budgetLevel: string, basePrice: number) {
    setLoadingRates(true);
    try {
      setRates(await compareRates({ hotel_name: hotelName, destination: dest, budget_level: budgetLevel, base_price: basePrice }));
    } catch { setRates([]); }
    finally { setLoadingRates(false); }
  }

  async function handleGenerate(e?: React.FormEvent) {
    e?.preventDefault();
    if (!destination.trim()) return;
    setLoading(true);
    setError(null);
    setItinerary(null);
    setRates([]);
    try {
      const result = await generateItinerary({ destination: destination.trim(), budget, duration_days: days });
      setItinerary(result);
      setActiveDay(0);
      if (result.days[0]) {
        fetchRates(result.days[0].accommodation.name, result.destination, budget, result.days[0].accommodation.price_per_night_inr);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate itinerary");
    } finally { setLoading(false); }
  }

  function handleDayChange(idx: number) {
    setActiveDay(idx);
    if (itinerary?.days[idx]) {
      const d = itinerary.days[idx];
      fetchRates(d.accommodation.name, itinerary.destination, budget, d.accommodation.price_per_night_inr);
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[380px_1fr] gap-6 items-start">

      {/* ── Form Card ─────────────────────────────────────────────────────── */}
      <div className="rounded-3xl bg-slate-900/80 border border-slate-700/60 backdrop-blur-sm p-6 shadow-2xl shadow-black/40 sticky top-24">
        <form onSubmit={handleGenerate} className="space-y-5">
          {/* Destination */}
          <div>
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-widest block mb-2">
              Destination
            </label>
            <input
              type="text"
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              placeholder="e.g. Varkala, Kerala"
              className="w-full px-4 py-3 rounded-xl bg-slate-800 border border-slate-600 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500/50 transition-colors"
              required
            />
          </div>

          {/* Budget */}
          <div>
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-widest block mb-2">
              Budget
            </label>
            <div className="flex flex-col gap-2">
              {BUDGET_OPTIONS.map((b) => (
                <button key={b.value} type="button" onClick={() => setBudget(b.value)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl border transition-all text-left ${
                    budget === b.value
                      ? `bg-gradient-to-r ${b.color} ${b.ring} border`
                      : "border-slate-700 hover:border-slate-600 bg-slate-800/40"
                  }`}
                >
                  <span className="text-xl">{b.icon}</span>
                  <div>
                    <p className={`text-sm font-semibold ${budget === b.value ? "text-white" : "text-slate-300"}`}>{b.label}</p>
                    <p className="text-xs text-slate-500">{b.sub}</p>
                  </div>
                  {budget === b.value && (
                    <span className="ml-auto text-xs font-bold text-violet-400">✓</span>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Duration */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-widest">
                Duration
              </label>
              <span className="text-sm font-bold text-white">{days} {days === 1 ? "day" : "days"}</span>
            </div>
            <input type="range" min={1} max={7} value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="w-full h-1.5 rounded-full appearance-none cursor-pointer accent-violet-500 bg-slate-700"
            />
            <div className="flex justify-between text-[10px] text-slate-600 mt-1">
              {Array.from({ length: 7 }, (_, i) => <span key={i}>{i+1}</span>)}
            </div>
          </div>

          {error && (
            <div className="rounded-xl bg-rose-900/30 border border-rose-700/50 px-4 py-3 text-sm text-rose-400">
              {error}
            </div>
          )}

          <button type="submit" disabled={loading}
            className="w-full py-3.5 rounded-xl font-bold text-sm transition-all disabled:opacity-50
                       bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500
                       text-white shadow-lg shadow-violet-900/30 hover:shadow-violet-900/50"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2.5">
                <span className="h-4 w-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                Gemini is planning your trip…
              </span>
            ) : "✨ Generate Itinerary"}
          </button>
        </form>
      </div>

      {/* ── Results ───────────────────────────────────────────────────────── */}
      {itinerary ? (
        <div className="space-y-5">
          {/* Summary header */}
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <h2 className="text-xl font-extrabold text-white">{itinerary.destination}</h2>
              <p className="text-sm text-slate-400">{itinerary.duration_days}-day itinerary · {BUDGET_OPTIONS.find(b => b.value === budget)?.label} budget</p>
            </div>
          </div>

          {/* Day tabs */}
          <div className="flex gap-2 flex-wrap">
            {itinerary.days.map((d, i) => (
              <button key={i} onClick={() => handleDayChange(i)}
                className={`px-5 py-2 rounded-xl text-sm font-semibold transition-all ${
                  activeDay === i
                    ? "bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white shadow-md shadow-violet-900/30"
                    : "bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white"
                }`}
              >
                Day {d.day_number}
              </button>
            ))}
          </div>

          {/* Day content */}
          {itinerary.days[activeDay] && (
            <DayView day={itinerary.days[activeDay]} rates={rates} loadingRates={loadingRates} />
          )}
        </div>
      ) : (
        /* Empty state */
        !loading && (
          <div className="hidden lg:flex flex-col items-center justify-center py-24 text-center gap-4">
            <div className="h-20 w-20 rounded-3xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-4xl">
              🧳
            </div>
            <div>
              <p className="text-lg font-semibold text-slate-300">Your itinerary will appear here</p>
              <p className="text-sm text-slate-500 mt-1">Fill in the form and hit Generate</p>
            </div>
            <div className="grid grid-cols-3 gap-3 mt-4 max-w-sm w-full">
              {["📍 Curated spots", "🍽️ Local food", "🏨 Best stays"].map((f) => (
                <div key={f} className="rounded-xl bg-slate-900/60 border border-slate-800 px-3 py-3 text-xs text-slate-400 text-center">
                  {f}
                </div>
              ))}
            </div>
          </div>
        )
      )}
    </div>
  );
}
