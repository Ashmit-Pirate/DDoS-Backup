from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.schemas import DetectRequest, DetectResponse
from db.database import get_db
from db.models import Detection
from db.redis_client import record_flow_stats
from detection.model_loader import get_model_bundle
from detection.feature_mapper import map_features
from detection.prediction import predict_flow

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
    Receives flow feature payload, runs the two-stage ML detection cascade:
    1. Binary LightGBM gatekeeper
    2. Multiclass XGBoost investigator (if gatekeeper flags Attack)

    Updates Redis flow counters on every request.
    If the flow is classified as Attack, writes an audit record to the `detections` database table.
    If the flow is Benign, no database row is written.
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

    # 3. Update Redis flow stats
    try:
        await record_flow_stats(is_benign=is_benign)
    except Exception as e:
        # Non-fatal log or pass if Redis is transiently unavailable in testing
        print(f"Warning: Failed to update Redis counters: {e}")

    # 4. If Attack, persist record to PostgreSQL detections table
    if not is_benign:
        try:
            record = Detection(
                source_ip=payload.source_ip,
                gatekeeper_confidence=gatekeeper_confidence,
                predicted_class=predicted_class,
                confidence=confidence,
            )
            db.add(record)
            db.commit()
            db.refresh(record)
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database write failed: {str(e)}",
            )

    return DetectResponse(
        predicted_class=predicted_class,
        confidence=confidence,
        gatekeeper_confidence=gatekeeper_confidence,
    )
