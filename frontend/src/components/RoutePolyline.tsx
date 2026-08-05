"use client";

import { useMemo } from "react";
import { Source, Layer } from "react-map-gl/maplibre";
import polyline from "@mapbox/polyline";

interface RoutePolylineProps {
  encodedPolyline: string;
}

/**
 * Renders a two-layer route line on the MapLibre canvas:
 *  - a wide blurred layer for the glow halo
 *  - a narrow crisp line for the actual route path
 */
export default function RoutePolyline({ encodedPolyline }: RoutePolylineProps) {
  const geojson = useMemo(() => {
    // @mapbox/polyline returns [[lat, lng], ...]; GeoJSON wants [lng, lat]
    const coords = polyline.decode(encodedPolyline).map(([lat, lng]) => [lng, lat]);
    return {
      type: "Feature" as const,
      geometry: { type: "LineString" as const, coordinates: coords },
      properties: {},
    };
  }, [encodedPolyline]);

  return (
    <Source id="route-source" type="geojson" data={geojson}>
      {/* Glow halo — wide, blurred, low opacity */}
      <Layer
        id="route-glow"
        type="line"
        paint={{
          "line-color": "#10b981",
          "line-width": 14,
          "line-opacity": 0.22,
          "line-blur": 8,
        }}
        layout={{ "line-join": "round", "line-cap": "round" }}
      />
      {/* Solid route line */}
      <Layer
        id="route-line"
        type="line"
        paint={{
          "line-color": "#10b981",
          "line-width": 3.5,
          "line-opacity": 0.92,
        }}
        layout={{ "line-join": "round", "line-cap": "round" }}
      />
    </Source>
  );
}
