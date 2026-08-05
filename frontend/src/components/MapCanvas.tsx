'use client';

import { useState, useCallback } from 'react';
import Map, { Marker } from 'react-map-gl/maplibre';
import type { ViewStateChangeEvent } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import TripPlannerPanel from './TripPlannerPanel';
import WaypointMarker from './WaypointMarker';
import RoutePolyline from './RoutePolyline';
import NavBar from './NavBar';
import type { TripPlanResponse } from '@/lib/types';

const DEFAULT_VIEW = {
  longitude: 7.6586,
  latitude: 45.9763,
  zoom: 7,
  bearing: 0,
  pitch: 40,
};

export default function MapCanvas({
  initialDestLat,
  initialDestLng,
  initialDestName,
}: {
  initialDestLat?: number;
  initialDestLng?: number;
  initialDestName?: string;
}) {
  const [viewState, setViewState] = useState(
    initialDestLat != null && initialDestLng != null
      ? { ...DEFAULT_VIEW, longitude: initialDestLng, latitude: initialDestLat, zoom: 9, pitch: 0 }
      : DEFAULT_VIEW,
  );
  const [tripResult, setTripResult]     = useState<TripPlanResponse | null>(null);
  const [originPin, setOriginPin]       = useState<[number, number] | null>(null);
  const [destPin, setDestPin]           = useState<[number, number] | null>(
    initialDestLat != null && initialDestLng != null
      ? [initialDestLng, initialDestLat]
      : null,
  );

  const onMove = useCallback((evt: ViewStateChangeEvent) => {
    setViewState(evt.viewState);
  }, []);

  function handleCoordinatesChange(
    origin: [number, number] | null,
    dest: [number, number] | null,
  ) {
    setOriginPin(origin);
    setDestPin(dest);
  }

  function handleTripPlanned(result: TripPlanResponse) {
    setTripResult(result);
    // Fly to midpoint between origin and dest pins if available
    if (originPin && destPin) {
      setViewState((v) => ({
        ...v,
        longitude: (originPin[0] + destPin[0]) / 2,
        latitude:  (originPin[1] + destPin[1]) / 2,
        zoom: 6,
      }));
    }
  }

  return (
    <div className="relative w-full h-screen overflow-hidden">
      <Map
        {...viewState}
        onMove={onMove}
        mapStyle="https://tiles.openfreemap.org/styles/liberty"
        style={{ width: '100%', height: '100%' }}
      >
        {/* Origin pin */}
        {originPin && (
          <Marker longitude={originPin[0]} latitude={originPin[1]} anchor="bottom">
            <div className="flex flex-col items-center">
              <span className="h-4 w-4 rounded-full bg-sky-500 border-2 border-white shadow-lg" />
              <span className="text-[10px] text-white font-bold bg-sky-600 rounded px-1 mt-0.5">A</span>
            </div>
          </Marker>
        )}

        {/* Destination pin */}
        {destPin && (
          <Marker longitude={destPin[0]} latitude={destPin[1]} anchor="bottom">
            <div className="flex flex-col items-center">
              <span className="h-4 w-4 rounded-full bg-rose-500 border-2 border-white shadow-lg" />
              <span className="text-[10px] text-white font-bold bg-rose-600 rounded px-1 mt-0.5">B</span>
            </div>
          </Marker>
        )}

        {/* Route polyline (glow effect) */}
        {tripResult?.encoded_polyline && (
          <RoutePolyline encodedPolyline={tripResult.encoded_polyline} />
        )}

        {/* Scenic anchor waypoints from backend */}
        {tripResult?.waypoints.map((wp, i) => (
          <WaypointMarker key={i} waypoint={wp} />
        ))}
      </Map>

      <NavBar />
      <TripPlannerPanel
        onTripPlanned={handleTripPlanned}
        onCoordinatesChange={handleCoordinatesChange}
        initialDestLat={initialDestLat}
        initialDestLng={initialDestLng}
        initialDestName={initialDestName}
      />
    </div>
  );
}
