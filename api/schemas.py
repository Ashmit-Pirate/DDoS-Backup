from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, model_validator


class DetectRequest(BaseModel):
    source_ip: str = Field(default="127.0.0.1", description="Source IP address of the traffic flow")
    features: Dict[str, Any] = Field(
        default_factory=dict,
        description="Dictionary of 77 flow features matching feature_columns.pkl",
    )

    @model_validator(mode="before")
    @classmethod
    def parse_input_features(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # If payload contains 'features' key, use it
            if "features" in data and isinstance(data["features"], dict):
                return data
            # If payload is a flat dictionary of features + optional source_ip
            source_ip = data.get("source_ip", "127.0.0.1")
            feature_dict = {k: v for k, v in data.items() if k != "source_ip"}
            return {"source_ip": source_ip, "features": feature_dict}
        return data


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


class HealthResponse(BaseModel):
    status: str = "ok"
    database: Optional[str] = None
    redis: Optional[str] = None
    models_loaded: bool = True
