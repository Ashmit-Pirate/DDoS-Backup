from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class FlowMetadata(BaseModel):
    source_ip: str = Field(description="Source IP address of the traffic flow")
    destination_ip: str = Field(description="Destination IP address of the traffic flow")
    source_port: int = Field(description="Source port number")
    destination_port: int = Field(description="Destination port number")


class DetectRequest(BaseModel):
    metadata: FlowMetadata = Field(
        description="Flow metadata containing source and destination IPs and ports"
    )
    features: Dict[str, Any] = Field(
        description="Dictionary of 77 flow features matching feature_columns.pkl"
    )


class DecisionInfo(BaseModel):
    """Decision engine output included in the detect response."""
    risk_score: int = Field(description="Numeric risk score (0-100)")
    severity: str = Field(description="Risk severity bucket: LOW, MEDIUM, or HIGH")
    action: str = Field(description="Decision action: ALLOW, MONITOR, or MITIGATE")


class MitigationInfo(BaseModel):
    """Mitigation action details included in the detect response when action=MITIGATE."""
    id: str = Field(description="UUID of the mitigation_actions row")
    attack_type: str = Field(description="Attack type that triggered mitigation")
    action_type: str = Field(description="Mitigation action type from the policy table")
    status: str = Field(description="Mitigation status (always SIMULATED this session)")
    expires_at: Optional[str] = Field(
        default=None, description="ISO timestamp when the cooldown expires"
    )


class DetectResponse(BaseModel):
    predicted_class: str = Field(
        description="Predicted traffic class (Benign, LDAP, MSSQL, NetBIOS, Portmap, Syn, UDP, UDPLag)"
    )
    confidence: float = Field(
        description="Confidence probability of the predicted class (0.0 to 1.0)"
    )
    gatekeeper_confidence: float = Field(
        description="Stage 1 Binary LightGBM attack probability confidence"
    )
    # Session 2 additions — None for Benign flows, populated for attacks
    decision: Optional[DecisionInfo] = Field(
        default=None, description="Decision engine output (None for Benign flows)"
    )
    mitigation: Optional[MitigationInfo] = Field(
        default=None, description="Mitigation action details (None unless action=MITIGATE)"
    )


class HealthResponse(BaseModel):
    status: str = "ok"
    database: Optional[str] = None
    redis: Optional[str] = None
    models_loaded: bool = True


# Session 3: WebSocket Event Envelope and REST endpoints

class TelemetryData(BaseModel):
    time: str
    timestamp: int
    incoming: int
    origin: int
    baseline: int
    event: Optional[str] = None

class DetectionData(BaseModel):
    prediction: str
    confidence: float
    risk: str

class MitigationData(BaseModel):
    id: str
    name: str
    status: str
    result: str
    sourceIp: str

class StatusChangeData(BaseModel):
    status: str

class WsEnvelope(BaseModel):
    type: str  # telemetry | detection | mitigation | status_change
    timestamp: str
    data: Dict[str, Any]

class RuntimeSystemConfig(BaseModel):
    targetApplication: str
    environment: str
    mitigationMode: str
    telemetryRefreshRateMs: int
    serverAvailability: int
    baselineRequestRate: int
    baselineEntropy: int

class Incident(BaseModel):
    id: str
    status: str
    type: str
    severity: str
    start: str
    detectionTime: str
    mitigationTime: str
    duration: str

class LogEvent(BaseModel):
    id: str
    time: str
    severity: str
    component: str
    message: str
    incidentId: Optional[str] = None

class EventsResponse(BaseModel):
    incidents: list[Incident]
    logs: list[LogEvent]

