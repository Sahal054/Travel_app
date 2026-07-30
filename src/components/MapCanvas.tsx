'use client';

import { useState, useCallback } from 'react';
import Map, { Marker } from 'react-map-gl';
import type { ViewStateChangeEvent } from 'react-map-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

// Swiss Alps — Matterhorn area
const INITIAL_VIEW_STATE = {
  longitude: 7.6586,
  latitude: 45.9763,
  zoom: 9,
  bearing: 0,
  pitch: 40,
};

// Placeholder for the first scenic anchor the backend will return
const SCENIC_PLACEHOLDER = {
  longitude: 7.6586,
  latitude: 45.9763,
  name: 'Matterhorn Viewpoint',
};

export default function MapCanvas() {
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE);

  const onMove = useCallback((evt: ViewStateChangeEvent) => {
    setViewState(evt.viewState);
  }, []);

  return (
    <div className="w-full h-screen">
      <Map
        {...viewState}
        onMove={onMove}
        mapStyle="mapbox://styles/mapbox/outdoors-v12"
        mapboxAccessToken={process.env.NEXT_PUBLIC_MAPBOX_TOKEN}
        style={{ width: '100%', height: '100%' }}
      >
        <Marker
          longitude={SCENIC_PLACEHOLDER.longitude}
          latitude={SCENIC_PLACEHOLDER.latitude}
          anchor="bottom"
        >
          <div
            title={SCENIC_PLACEHOLDER.name}
            className="relative flex items-center justify-center"
          >
            {/* Outer pulse ring */}
            <span className="absolute inline-flex h-5 w-5 animate-ping rounded-full bg-emerald-400 opacity-60" />
            {/* Pin dot */}
            <span className="relative inline-flex h-4 w-4 rounded-full bg-emerald-500 border-2 border-white shadow-lg" />
          </div>
        </Marker>
      </Map>
    </div>
  );
}
