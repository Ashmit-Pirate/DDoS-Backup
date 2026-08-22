import { SystemState, TrafficPoint, PredictionResult, MitigationAction, Incident, LogEvent, RuntimeSystemConfig } from "@/types/sage";

export interface SimulationState {
  state: SystemState;
  trafficData: TrafficPoint[];
  prediction: PredictionResult;
  mitigations: MitigationAction[];
  incidents: Incident[];
  logs: LogEvent[];
  config: RuntimeSystemConfig;
  isSimulating: boolean;
  simIntensity: "LOW" | "MEDIUM" | "HIGH";
}

export const defaultPrediction: PredictionResult = {
  prediction: "Benign",
  confidence: 99.9,
  risk: "LOW",
};

export const defaultConfig: RuntimeSystemConfig = {
  targetApplication: "demo-app.sage.local",
  environment: "Demo / Sandbox",
  mitigationMode: "Simulation Only",
  telemetryRefreshRateMs: 1000,
  serverAvailability: 99.9,
  baselineRequestRate: 4200,
  baselineEntropy: 0.82
};

export const generateBaseTraffic = (count: number, baseline: number): TrafficPoint[] => {
  const now = Date.now();
  return Array.from({ length: count }).map((_, i) => {
    const timestamp = now - (count - i) * 1000;
    const date = new Date(timestamp);
    const base = baseline + Math.random() * 400 - 200;
    return {
      time: `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`,
      timestamp,
      incoming: base,
      origin: base,
      baseline: baseline,
    };
  });
};

export const createLog = (log: Omit<LogEvent, "id" | "time">): LogEvent => {
  const date = new Date();
  return {
    ...log,
    id: Math.random().toString(36).substring(7),
    time: `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}.${date.getMilliseconds().toString().padStart(3, '0')}`,
  };
};
