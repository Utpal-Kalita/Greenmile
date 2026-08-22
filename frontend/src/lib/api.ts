import type {
  Benchmark,
  MapPayload,
  OptimizationRun,
  Scenario,
  StageEvent,
  Stop,
} from "@/types/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: unknown,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
  });
  if (!response.ok) {
    let detail: unknown;
    try {
      detail = await response.json();
    } catch {
      detail = await response.text();
    }
    throw new ApiError(
      `Greenmile API request failed (${response.status})`,
      response.status,
      detail,
    );
  }
  return response.json() as Promise<T>;
}

export const api = {
  getDemoScenario: () => request<Scenario>("/api/scenarios/demo"),
  getStops: (scenarioId: string) =>
    request<Stop[]>(`/api/scenarios/${scenarioId}/stops`),
  getScenarioMap: (scenarioId: string) =>
    request<MapPayload>(`/api/scenarios/${scenarioId}/map`),
  createRun: (scenarioId: string) =>
    request<OptimizationRun>("/api/optimization-runs", {
      method: "POST",
      body: JSON.stringify({ scenario_id: scenarioId }),
    }),
  getRun: (runId: string) =>
    request<OptimizationRun>(`/api/optimization-runs/${runId}`),
  getRunMap: (runId: string) =>
    request<MapPayload>(`/api/optimization-runs/${runId}/map`),
  getBenchmarks: () => request<Benchmark[]>("/api/benchmarks"),
  runBenchmarks: (scenarioId: string, workloads: number[]) =>
    request<Benchmark[]>("/api/benchmarks", {
      method: "POST",
      body: JSON.stringify({
        scenario_id: scenarioId,
        workloads,
        repetitions: 3,
      }),
    }),
  submitEvent: (
    runId: string,
    eventType: string,
    stopId: string | null,
    payload: Record<string, unknown> = {},
  ) =>
    request<OptimizationRun>(`/api/optimization-runs/${runId}/events`, {
      method: "POST",
      body: JSON.stringify({ event_type: eventType, stop_id: stopId, payload }),
    }),
};

export function streamRunEvents(
  runId: string,
  onEvent: (event: StageEvent) => void,
  onError: () => void,
): () => void {
  const source = new EventSource(
    `${API_URL}/api/optimization-runs/${runId}/events/stream`,
  );
  const eventNames = [
    "RUN_CREATED",
    "VALIDATING",
    "LOADING_DATA",
    "CLUSTERING",
    "BUILDING_ROUTE",
    "OPTIMIZING",
    "CHECKING_CONSTRAINTS",
    "CALCULATING_METRICS",
    "PERSISTING",
    "ROUTE_READY",
    "AI_ANALYSIS_STARTED",
    "AI_ANALYSIS_COMPLETE",
    "AI_ANALYSIS_FAILED",
    "DELIVERY_COMPLETED",
    "DELIVERY_FAILED",
    "RETURN_READY",
    "RETURN_COLLECTED",
    "RETURN_CANCELLED",
    "STOP_CANCELLED",
    "CAPACITY_CHANGED",
    "TRAFFIC_DELAY",
    "DRIVER_DELAY",
    "REOPTIMIZING",
    "ROUTE_UPDATED",
  ];
  const listener = (event: MessageEvent<string>) =>
    onEvent(JSON.parse(event.data) as StageEvent);
  eventNames.forEach((name) =>
    source.addEventListener(name, listener as EventListener),
  );
  source.onerror = onError;
  return () => source.close();
}
