'use client';

import { Marker } from 'react-map-gl/maplibre';
import type { InjectedWaypoint } from '@/lib/types';

interface Props {
  waypoint: InjectedWaypoint;
}

export default function WaypointMarker({ waypoint }: Props) {
  return (
    <Marker longitude={waypoint.lng} latitude={waypoint.lat} anchor="bottom">
      <div className="group relative flex flex-col items-center">
        <div className="relative flex items-center justify-center mb-1">
          <span className="absolute inline-flex h-6 w-6 animate-ping rounded-full bg-emerald-400 opacity-50" />
          <span className="relative inline-flex h-4 w-4 rounded-full bg-emerald-500 border-2 border-white shadow-lg" />
        </div>
        <span className="hidden group-hover:block absolute bottom-full mb-2 whitespace-nowrap
          rounded-md bg-slate-900/90 px-2 py-1 text-xs text-white shadow-lg border border-slate-700">
          {waypoint.name}
        </span>
      </div>
    </Marker>
  );
}
