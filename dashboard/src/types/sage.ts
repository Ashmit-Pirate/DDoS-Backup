export type SystemState = 
  | "NORMAL" 
  | "ATTACK_DETECTED" 
  | "CLASSIFIED" 
  | "MITIGATING" 
  | "RECOVERING" 
  | "RECOVERED";

export type AttackClass = "Benign" | "LDAP" | "MSSQL" | "NetBIOS" | "Portmap" | "Syn" | "UDP" | "UDPLag";

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH";
export type MitigationStatus = "PLANNED" | "SIMULATED" | "ACTIVE" | "COMPLETED";
export type LogSeverity = "INFO" | "WARN" | "HIGH" | "ALERT" | "OK";
export type IncidentSeverity = "LOW" | "MEDIUM" | "HIGH";

// Runtime System Configuration (Managed by Store/Backend)
export interface RuntimeSystemConfig {
  targetApplication: string;
  environment: string;
  mitigationMode: "Simulation Only" | "Active Enforcement";
  telemetryRefreshRateMs: number;
  serverAvailability: number;
  baselineRequestRate: number;
  baselineEntropy: number;
}

// Static Model Metadata (Managed by Config)
export interface ModelMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
}

export interface ModelMetadata {
  name: string;
  featureCount: number;
  trainedClasses: number;
  supportedClasses: AttackClass[];
  modelArtifactPath: string;
  featureSchemaPath: string;
  metrics: ModelMetrics;
}

// Telemetry & Runtime Data
export interface TrafficPoint {
  time: string;
  timestamp: number;
  incoming: number;
  origin: number;
  baseline: number;
  event?: string;
}

export interface PredictionResult {
  prediction: AttackClass;
  confidence: number;
  risk: RiskLevel;
}

export interface MitigationAction {
  id: string;
  name: string;
  status: MitigationStatus;
  result: string;
  sourceIp?: string;
}

export interface Incident {
  id: string;
  status: "ACTIVE" | "RESOLVED";
  type: AttackClass | "UNKNOWN";
  severity: IncidentSeverity;
  start: string;
  detectionTime: string;
  mitigationTime: string;
  duration: string;
}

export interface LogEvent {
  id: string;
  time: string;
  severity: LogSeverity;
  component: string;
  message: string;
  incidentId?: string;
}
