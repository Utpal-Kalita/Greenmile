export type StopKind = "delivery" | "return" | "warehouse";
export type RiskLevel = "low" | "medium" | "high";

export interface Stop {
  id: string;
  name: string;
  address: string;
  kind: StopKind;
  window: string;
  eta: string;
  packages: number;
  weightKg: number;
  risk?: RiskLevel;
  riskScore?: number;
  note?: string;
  x: number;
  y: number;
}

export interface EngineStage {
  id: string;
  label: string;
  detail: string;
  duration: string;
}

export interface Benchmark {
  workload: number;
  before: {
    routeReady: number;
    fullResult: number;
    routeQuality: number;
    aiBlocking: boolean;
  };
  after: {
    routeReady: number;
    fullResult: number;
    routeQuality: number;
    aiBlocking: boolean;
  };
}

export interface EngineEvent {
  timestamp: string;
  type: string;
  value: string;
  status: "complete" | "active";
}
