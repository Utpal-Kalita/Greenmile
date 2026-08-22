export type ScenarioStatus = "DRAFT" | "READY" | "ARCHIVED";
export type StopType = "DELIVERY" | "RETURN" | "PICKUP";
export type RunStatus =
  | "QUEUED"
  | "VALIDATING"
  | "OPTIMIZING"
  | "VALIDATING_ROUTE"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED";
export type RouteAction =
  "DEPOT_START" | "DELIVER" | "PICKUP" | "RETURN" | "DEPOT_END";
export type ProviderStatus = "AVAILABLE" | "UNAVAILABLE";

export interface Scenario {
  id: string;
  name: string;
  description: string;
  city: string;
  status: ScenarioStatus;
  depot_lat: number;
  depot_lng: number;
  depot_address: string;
  vehicle_count: number;
  vehicle_capacity_kg: number;
  vehicle_capacity_l: number;
  provenance: {
    kind?: string;
    generator?: string;
    seed?: number;
    claims?: string;
    [key: string]: unknown;
  };
  is_demo: boolean;
  created_at: string;
  updated_at: string;
  stop_count: number;
  delivery_count: number;
  return_count: number;
}

export interface Stop {
  id: string;
  scenario_id: string;
  external_id: string;
  type: StopType;
  address: string;
  lat: number;
  lng: number;
  weight_kg: number;
  volume_l: number;
  time_window_start: string;
  time_window_end: string;
  service_time_seconds: number;
  status: string;
  data_provenance: string;
}

export interface Vehicle {
  id: string;
  vehicle_code: string;
  capacity_kg: number;
  capacity_l: number;
  fuel_type: string;
  fuel_efficiency_km_per_l: number;
  driver_hourly_cost: number;
  status: string;
}

export interface RouteStop {
  sequence_number: number;
  vehicle_sequence: number;
  stop_id: string | null;
  external_id: string;
  name: string;
  address: string;
  lat: number;
  lng: number;
  type: StopType | "WAREHOUSE";
  action: RouteAction;
  arrival_time: string;
  departure_time: string;
  load_before_kg: number;
  load_after_kg: number;
  load_before_l: number;
  load_after_l: number;
  distance_from_previous_km: number;
  status: string;
}

export interface MetricPair {
  before: number;
  after: number;
  saved: number;
  saved_percent: number;
}
export interface RunMetrics {
  distance: {
    before_km: number;
    after_km: number;
    saved_km: number;
    saved_percent: number;
  };
  fuel_litres: MetricPair;
  fuel_cost: MetricPair;
  co2_kg: MetricPair;
  driver_hours: MetricPair;
  labor_cost: MetricPair;
  total_cost: MetricPair;
}
export interface ConstraintViolation {
  type: string;
  message: string;
  stop_id?: string | null;
  amount_kg?: number | null;
  amount_l?: number | null;
}
export interface StageEvent {
  id: string;
  event_type: string;
  stop_id: string | null;
  payload: Record<string, unknown>;
  duration_ms: number | null;
  created_at: string;
}
export interface ProviderAvailability {
  status: ProviderStatus;
  provider: string | null;
  message: string;
  model: string | null;
  model_version: string | null;
  latency_ms: number | null;
  summary: string | null;
  predictions: Array<Record<string, unknown>>;
  recommendations: Array<Record<string, unknown>>;
}
export interface PackingItem {
  sequence: number;
  stop_id: string;
  action: RouteAction;
  weight_kg: number;
  volume_l: number;
  zone: "DELIVERY" | "RETURN_ACCESS";
}
export interface PackingPlan {
  capacity_kg: number;
  capacity_l: number;
  initial_load_kg: number;
  initial_load_l: number;
  utilization_percent: number;
  items: PackingItem[];
}

export interface OptimizationRun {
  id: string;
  run_id: string;
  scenario: Scenario;
  vehicles: Vehicle[];
  status: RunStatus;
  system_state: string;
  algorithm_version: string;
  routing_provider: string;
  started_at: string | null;
  completed_at: string | null;
  stop_count: number;
  cluster_count: number;
  latency_ms: number | null;
  stage_timings: Record<string, number>;
  route: RouteStop[];
  metrics: RunMetrics | null;
  constraints: { feasible: boolean; violations: ConstraintViolation[] };
  packing: PackingPlan | null;
  prediction: ProviderAvailability;
  intelligence: ProviderAvailability;
  events: StageEvent[];
  error_message: string | null;
}

export type GeoJSONPosition = [number, number];

export interface GeoJSONGeometry {
  type: "Point" | "LineString";
  coordinates: GeoJSONPosition | GeoJSONPosition[];
}

export interface GeoJSONFeature {
  type: "Feature";
  geometry: GeoJSONGeometry;
  properties: Record<string, unknown>;
}

export interface GeoJSONFeatureCollection {
  type: "FeatureCollection";
  features: GeoJSONFeature[];
}

export interface MapPayload {
  scenario_id: string;
  run_id: string | null;
  system_state: string;
  map: {
    center: { lat: number; lng: number };
    bounds: { south: number; west: number; north: number; east: number };
  };
  stops: GeoJSONFeatureCollection;
  warehouse: GeoJSONFeature;
  routes: {
    baseline_delivery: GeoJSONFeatureCollection;
    baseline_return: GeoJSONFeatureCollection;
    optimized: GeoJSONFeatureCollection;
  };
  events: GeoJSONFeatureCollection;
  metrics: RunMetrics | null;
  performance: {
    optimization_latency_ms: number | null;
    reoptimization_latency_ms: number | null;
  };
  intelligence: ProviderAvailability | null;
}

export interface Benchmark {
  id: string;
  scenario_id: string;
  dataset_name: string;
  dataset_version: string;
  stop_count: number;
  baseline_algorithm: string;
  optimized_algorithm: string;
  baseline_latency_ms: number;
  optimized_latency_ms: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  baseline_distance_km: number;
  optimized_distance_km: number;
  route_quality_delta: number;
  constraint_violations: number;
  memory_usage_mb: number;
  stage_timings: Record<string, number | number[]>;
  created_at: string;
}
