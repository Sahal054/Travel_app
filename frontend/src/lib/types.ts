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
  encoded_polyline?: string;
}

// ── Auth ────────────────────────────────────────────────────────────────────
export interface RegisterRequest {
  email: string;
  password: string;
  display_name?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user_id: number;
  display_name: string | null;
}

// ── TSP Optimize ────────────────────────────────────────────────────────────
export interface WaypointInput {
  lat: number;
  lng: number;
  name: string;
}

export interface OptimizeRequest {
  origin_lat: number;
  origin_lng: number;
  waypoints: WaypointInput[];
}

export interface OptimizedRoute {
  optimized_order: number[];
  ordered_waypoints: WaypointInput[];
  encoded_polyline: string;
  native_maps_url: string;
}

// ── Itinerary ───────────────────────────────────────────────────────────────
export interface Activity {
  time: string;
  period: string;
  name: string;
  type: string;
  duration_minutes: number;
  description: string;
  estimated_cost_inr: number;
  rating: number | null;
}

export interface Accommodation {
  name: string;
  type: string;
  price_per_night_inr: number;
  rating: number | null;
  address: string | null;
}

export interface ItineraryDay {
  day_number: number;
  theme: string;
  activities: Activity[];
  accommodation: Accommodation;
}

export interface ItineraryRequest {
  destination: string;
  budget: 'backpacker' | 'standard' | 'luxury';
  duration_days: number;
}

export interface ItineraryResponse {
  destination: string;
  duration_days: number;
  budget_level: string;
  days: ItineraryDay[];
  itinerary_id: number | null;
}

// ── Rates ───────────────────────────────────────────────────────────────────
export interface OTARate {
  provider: string;
  logo_slug: string;
  price_per_night_inr: number;
  currency: string;
  rating: number | null;
  review_count: number | null;
  deep_link: string;
  is_best_deal: boolean;
  badge: string | null;
}

export interface RatesRequest {
  hotel_name: string;
  destination: string;
  budget_level?: string;
  base_price?: number;
}
