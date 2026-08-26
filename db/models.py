import uuid
from sqlalchemy import (
    Column,
    String,
    Numeric,
    Integer,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Index,
    JSON,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from db.database import Base

# Universal JSON type (JSONB on PostgreSQL, JSON on SQLite)
JSON_FIELD = JSONB().with_variant(JSON(), "sqlite")


class Detection(Base):
    __tablename__ = "detections"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    source_ip = Column(String, nullable=False)
    gatekeeper_confidence = Column(Numeric(5, 4), nullable=True)
    predicted_class = Column(String, nullable=False)
    confidence = Column(Numeric(5, 4), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "predicted_class IN ('Benign','LDAP','MSSQL','NetBIOS','Portmap','Syn','UDP','UDPLag')",
            name="check_detection_predicted_class",
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1",
            name="check_detection_confidence_range",
        ),
        Index("idx_detections_time", "timestamp"),
    )


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    detection_id = Column(
        Uuid,
        ForeignKey("detections.id", ondelete="CASCADE"),
        nullable=False,
    )
    risk_score = Column(Integer, nullable=False)
    severity = Column(String, nullable=False)
    factors = Column(JSON_FIELD, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("risk_score BETWEEN 0 AND 100", name="check_risk_score_range"),
        CheckConstraint("severity IN ('LOW','MEDIUM','HIGH')", name="check_severity_values"),
    )


class MitigationAction(Base):
    __tablename__ = "mitigation_actions"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    risk_assessment_id = Column(
        Uuid,
        ForeignKey("risk_assessments.id", ondelete="CASCADE"),
        nullable=False,
    )
    attack_type = Column(String, nullable=False)
    action_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    source_ip = Column(String, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('PLANNED','SIMULATED','ACTIVE','COMPLETED')",
            name="check_mitigation_status_values",
        ),
        Index("idx_mitigation_source", "source_ip", "status"),
    )


class Event(Base):
    __tablename__ = "events"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    attack_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    confidence = Column(Numeric(5, 4), nullable=True)
    action = Column(String, nullable=True)
    status = Column(String, nullable=True)

    __table_args__ = (
        Index("idx_events_time", "timestamp"),
        Index("idx_events_attack_type", "attack_type"),
    )


class SystemStatus(Base):
    __tablename__ = "system_status"

    id = Column(Integer, primary_key=True, default=1)
    status = Column(String, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("id = 1", name="check_singleton_id"),
        CheckConstraint(
            "status IN ('NORMAL','ATTACK_DETECTED','CLASSIFIED','MITIGATING','RECOVERING','RECOVERED')",
            name="check_system_status_values",
        ),
    )


class Config(Base):
    __tablename__ = "config"

    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
