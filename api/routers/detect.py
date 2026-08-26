from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.schemas import DetectRequest, DetectResponse, DecisionInfo, MitigationInfo
from db.database import get_db
from db.models import Detection, RiskAssessment
from db.redis_client import record_flow_stats
from detection.model_loader import get_model_bundle
from detection.feature_mapper import map_features
from detection.prediction import predict_flow
from decision.decision_engine import evaluate as evaluate_decision
from mitigation.mitigation_engine import execute_mitigation

router = APIRouter(prefix="/api/v1", tags=["Detection"])


@router.post(
    "/detect",
    response_model=DetectResponse,
    status_code=status.HTTP_200_OK,
    summary="Classify traffic flow using two-stage ML cascade",
)
async def detect_flow(
    payload: DetectRequest,
    db: Session = Depends(get_db),
) -> DetectResponse:
    """
    Receives flow payload with nested metadata and 77-feature dictionary.
    Runs the two-stage ML detection cascade:
    1. Binary LightGBM gatekeeper
    2. Multiclass XGBoost investigator (if gatekeeper flags Attack)

    Then runs the Session 2 pipeline:
    3. Decision engine — risk scoring based on Redis state (rate, repeat, mitigation)
    4. If warranted, mitigation engine writes a SIMULATED mitigation action

    Updates Redis flow counters on every request.
    If the flow is classified as Attack, writes audit records to the
    `detections`, `risk_assessments`, and (if applicable) `mitigation_actions` tables.
    If the flow is Benign, no database row is written (only Redis stats counters).

    Note: `destination_ip`, `source_port`, and `destination_port` in `payload.metadata`
    are validated and accepted, but not persisted to the database per the current schema contract.
    """
    try:
        bundle = get_model_bundle()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model bundle not loaded: {str(e)}",
        )

    # 1. Reindex incoming features into the exact 77-column order
    features_vector = map_features(payload.features, bundle.feature_columns)

    # 2. Run two-stage ML cascade inference
    result = predict_flow(features_vector, bundle)
    predicted_class = result["predicted_class"]
    confidence = result["confidence"]
    gatekeeper_confidence = result["gatekeeper_confidence"]
    is_benign = (predicted_class == "Benign")

    # 3. Update Redis flow stats (every request, regardless of outcome)
    try:
        await record_flow_stats(is_benign=is_benign)
    except Exception as e:
        print(f"Warning: Failed to update Redis counters: {e}")

    # 4. Run decision engine
    #    For Benign: returns ALLOW immediately, no Redis state touched.
    #    For Attack: increments rate/detection counters, computes risk.
    try:
        decision = await evaluate_decision(result, payload.metadata.source_ip)
    except Exception as e:
        print(f"Warning: Decision engine failed: {e}")
        # Fallback: still return prediction without decision/mitigation
        decision = None

    # Build decision info for response
    decision_info = None
    if decision is not None:
        decision_info = DecisionInfo(
            risk_score=decision["risk_score"],
            severity=decision["severity"],
            action=decision["action"],
        )

    # 5. If Attack, persist Detection record to PostgreSQL
    detection_record = None
    if not is_benign:
        try:
            detection_record = Detection(
                source_ip=payload.metadata.source_ip,
                gatekeeper_confidence=gatekeeper_confidence,
                predicted_class=predicted_class,
                confidence=confidence,
            )
            db.add(detection_record)
            db.flush()  # Flush to get the id for FK references
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database write failed: {str(e)}",
            )

    # 6. If Attack with a valid decision, persist RiskAssessment record
    risk_assessment_record = None
    if not is_benign and decision is not None and detection_record is not None:
        try:
            risk_assessment_record = RiskAssessment(
                detection_id=detection_record.id,
                risk_score=decision["risk_score"],
                severity=decision["severity"],
                factors=decision["factors"] or {},
            )
            db.add(risk_assessment_record)
            db.flush()  # Flush to get the id for FK references
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Risk assessment write failed: {str(e)}",
            )

    # 7. If decision is MITIGATE, run mitigation engine
    mitigation_info = None
    if (
        decision is not None
        and decision.get("action") == "MITIGATE"
        and risk_assessment_record is not None
    ):
        try:
            mitigation_record = await execute_mitigation(
                decision=decision,
                prediction=result,
                source_ip=payload.metadata.source_ip,
                risk_assessment_id=risk_assessment_record.id,
                db=db,
            )
            if mitigation_record is not None:
                mitigation_info = MitigationInfo(
                    id=str(mitigation_record.id),
                    attack_type=mitigation_record.attack_type,
                    action_type=mitigation_record.action_type,
                    status=mitigation_record.status,
                    expires_at=(
                        mitigation_record.expires_at.isoformat()
                        if mitigation_record.expires_at
                        else None
                    ),
                )
        except Exception as e:
            print(f"Warning: Mitigation engine failed: {e}")

    # 8. Commit all DB changes in one transaction
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database commit failed: {str(e)}",
        )

    # 9. Publish WebSocket Events
    if not is_benign:
        from api.events_publisher import publish_event
        
        risk = decision_info.severity if decision_info else "LOW"
        action = decision_info.action if decision_info else None

        # Publish detection event
        det_data = {
            "prediction": predicted_class,
            "confidence": float(confidence),
            "risk": risk
        }
        det_db_args = {
            "attack_type": predicted_class,
            "severity": risk,
            "confidence": float(confidence),
            "action": action,
            "status": None
        }
        await publish_event("detection", det_data, db=db, db_args=det_db_args)

        # Publish mitigation event if applicable
        if mitigation_info:
            action_names = {
                "RATE_LIMIT": "Connection rate limiting",
                "RATE_LIMIT_AND_FILTER": "UDP rate limiting + filtering",
                "RESTRICT_EXPOSURE": "Restrict exposure",
                "FILTER_AND_RATE_LIMIT": "Filtering + rate limiting",
                "RESTRICT_TRAFFIC": "Restrict unnecessary traffic"
            }
            name = action_names.get(mitigation_info.action_type, "Mitigation applied")
            result_str = f"Would apply {mitigation_info.action_type} to {payload.metadata.source_ip}"
            
            mit_data = {
                "id": mitigation_info.id,
                "name": name,
                "status": mitigation_info.status,
                "result": result_str,
                "sourceIp": payload.metadata.source_ip
            }
            mit_db_args = {
                "attack_type": predicted_class,
                "severity": risk,
                "confidence": float(confidence),
                "action": mitigation_info.action_type,
                "status": mitigation_info.status
            }
            await publish_event("mitigation", mit_data, db=db, db_args=mit_db_args)

    return DetectResponse(
        predicted_class=predicted_class,
        confidence=confidence,
        gatekeeper_confidence=gatekeeper_confidence,
        decision=decision_info,
        mitigation=mitigation_info,
    )
