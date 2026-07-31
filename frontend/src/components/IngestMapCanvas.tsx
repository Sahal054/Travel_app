'use client';

import { useState, useCallback } from 'react';
import Map, { Marker } from 'react-map-gl/maplibre';
import type { ViewStateChangeEvent } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import IngestPanel from './IngestPanel';
import NavBar from './NavBar';
import type { PlaceSummary } from '@/lib/types';

const DEFAULT_VIEW = {
  longitude: 20,
  latitude: 20,
  zoom: 1.8,
  bearing: 0,
  pitch: 0,
};

export default function IngestMapCanvas() {
  const [viewState, setViewState] = useState(DEFAULT_VIEW);
  const [place, setPlace]         = useState<PlaceSummary | null>(null);

  const onMove = useCallback((evt: ViewStateChangeEvent) => {
    setViewState(evt.viewState);
  }, []);

  function handlePlaceExtracted(p: PlaceSummary) {
    setPlace(p);
    setViewState((v) => ({ ...v, longitude: p.longitude, latitude: p.latitude, zoom: 12 }));
  }

  return (
    <div className="relative w-full h-screen overflow-hidden">
      <Map
        {...viewState}
        onMove={onMove}
        mapStyle="https://tiles.openfreemap.org/styles/liberty"
        style={{ width: '100%', height: '100%' }}
      >
        {place && (
          <Marker longitude={place.longitude} latitude={place.latitude} anchor="bottom">
            <div className="group relative flex flex-col items-center">
              <div className="relative flex items-center justify-center mb-1">
                <span className="absolute inline-flex h-6 w-6 animate-ping rounded-full bg-pink-400 opacity-50" />
                <span className="relative inline-flex h-4 w-4 rounded-full bg-pink-500 border-2 border-white shadow-lg" />
              </div>
              <span className="hidden group-hover:block absolute bottom-full mb-2 whitespace-nowrap
                rounded-md bg-slate-900/90 px-2 py-1 text-xs text-white shadow-lg border border-slate-700">
                {place.place_name}
              </span>
            </div>
          </Marker>
        )}
      </Map>

      <NavBar />
      <IngestPanel onPlaceExtracted={handlePlaceExtracted} />
    </div>
  );
}
