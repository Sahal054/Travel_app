export type RouteMode = 'quickest' | 'scenic';

export interface PlaceSummary {
  place_name: string;
  formatted_address: string | null;
  city: string | null;
  region: string | null;
  country: string | null;
  latitude: number;
  longitude: number;
  confidence: number;
}

export interface IngestReelResponse {
  status: string;
  message: string;
  reel_url: string | null;
  saved_reel_id: number | null;
  place_id: number | null;
  place_summary: PlaceSummary | null;
}

export interface TripPlanRequest {
  origin_lat: number;
  origin_lng: number;
  dest_lat: number;
  dest_lng: number;
  route_mode: RouteMode;
}

export interface InjectedWaypoint {
  name: string;
  lat: number;
  lng: number;
  poi_type: string;
}

export interface TripPlanResponse {
  route_status: string;
  injected_waypoints_count: number;
  injected_poi_names: string[];
  native_maps_url: string;
  waypoints: InjectedWaypoint[];
  cache_hit: boolean;
}
