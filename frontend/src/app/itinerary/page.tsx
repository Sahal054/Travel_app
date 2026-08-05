"use client";

import { Suspense } from "react";
import NavBar from "@/components/NavBar";
import ItineraryPanel from "@/components/ItineraryPanel";

export default function ItineraryPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      <NavBar />

      {/* Hero */}
      <div className="pt-24 pb-10 px-6 text-center">
        <div className="inline-flex items-center gap-2 bg-violet-500/10 border border-violet-500/20 rounded-full px-4 py-1.5 text-xs text-violet-300 font-medium mb-6">
          <span className="h-1.5 w-1.5 rounded-full bg-violet-400 animate-pulse" />
          Powered by Gemini AI
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-4">
          <span className="bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
            You save the spots.
          </span>
          <br />
          <span className="bg-gradient-to-r from-violet-400 via-fuchsia-400 to-pink-400 bg-clip-text text-transparent">
            We'll handle the rest.
          </span>
        </h1>
        <p className="text-slate-400 max-w-lg mx-auto text-base">
          Pick a destination, choose your vibe and budget — Gemini builds a complete day-by-day itinerary with local gems, food spots, and live hotel rates.
        </p>
      </div>

      {/* Main content */}
      <div className="max-w-5xl mx-auto px-4 pb-20">
        <Suspense>
          <ItineraryPanel />
        </Suspense>
      </div>
    </div>
  );
}
