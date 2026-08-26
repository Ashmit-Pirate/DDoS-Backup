import os
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from dotenv import load_dotenv

from db.database import engine
from db.redis_client import ping_redis, close_redis
from detection.model_loader import load_models, get_model_bundle
from api.routers.detect import router as detect_router
from api.routers.ws import router as ws_router
from api.routers.status import router as status_router
from api.routers.events import router as events_router
from api.routers.mitigation import router as mitigation_router
from api.routers.config import router as config_router
from api.schemas import HealthResponse

load_dotenv()


def get_allowed_origins() -> List[str]:
    """Parse ALLOWED_ORIGINS from environment, ensuring no wildcard is used."""
    raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    # Filter out wildcard '*' to strictly protect credentials and dashboard integrity
    filtered_origins = [o for o in origins if o != "*"]
    return filtered_origins if filtered_origins else ["http://localhost:3000"]


import asyncio
from datetime import datetime, timezone
from db.redis_client import get_traffic_stats
from db.database import SessionLocal
from db.models import Config
from api.events_publisher import publish_event

async def telemetry_loop():
    while True:
        refresh_rate_ms = 1000
        baseline_rate = 1000
        try:
            with SessionLocal() as db:
                rate_rec = db.query(Config).filter(Config.key == "telemetryRefreshRateMs").first()
                if rate_rec:
                    refresh_rate_ms = int(rate_rec.value)
                base_rec = db.query(Config).filter(Config.key == "baselineRequestRate").first()
                if base_rec:
                    baseline_rate = int(base_rec.value)
        except Exception:
            pass
            
        try:
            stats = await get_traffic_stats()
            now = datetime.now(timezone.utc)
            telemetry_data = {
                "time": now.strftime("%H:%M:%S"),
                "timestamp": int(now.timestamp() * 1000),
                "incoming": stats["total_count"],
                "origin": stats["benign_count"],
                "baseline": baseline_rate,
                "event": None
            }
            await publish_event("telemetry", telemetry_data, db=None, db_args=None)
        except Exception as e:
            print(f"Telemetry loop error: {e}")
            
        await asyncio.sleep(refresh_rate_ms / 1000.0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler:
    - Startup:
      1. Pre-loads both tuned ML models into memory once.
      2. Verifies PostgreSQL database connectivity (SELECT 1).
         (Note: Schema creation is strictly managed by Alembic, not create_all).
      3. Verifies Redis connectivity via ping.
      4. Starts the background telemetry loop.
    - Shutdown:
      1. Cancels the background telemetry loop.
      2. Closes Redis connection pool.
      3. Disposes database engine pool.
    """
    # 1. Load ML models once into memory
    try:
        load_models()
        print("ML Models successfully loaded into memory.")
    except Exception as e:
        print(f"Warning: ML model loading failed: {e}")

    # 2. Verify PostgreSQL connectivity
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("PostgreSQL connectivity verified.")
    except Exception as e:
        print(f"Warning: PostgreSQL connectivity check failed: {e}")

    # 3. Verify Redis connectivity
    try:
        redis_ok = await ping_redis()
        if redis_ok:
            print("Redis connectivity verified.")
        else:
            print("Warning: Redis ping returned false.")
    except Exception as e:
        print(f"Warning: Redis connectivity check failed: {e}")

    # 4. Start background telemetry loop
    telemetry_task = asyncio.create_task(telemetry_loop())

    yield

    # Shutdown
    telemetry_task.cancel()
    await close_redis()
    engine.dispose()
    print("Application shutdown: database and Redis pools closed.")


app = FastAPI(
    title="DDoS Protection System Backend",
    description="Adaptive DDoS detection, classification, and mitigation service for SIH26_206.",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS locked to dashboard origins
allowed_origins = get_allowed_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(detect_router)
app.include_router(ws_router)
app.include_router(status_router)
app.include_router(events_router)
app.include_router(mitigation_router)
app.include_router(config_router)

@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check endpoint",
    tags=["System"],
)
async def health_check() -> HealthResponse:
    """Returns 200 OK and connectivity status of backing services and ML models."""
    db_status = "connected"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"

    redis_status = "connected"
    try:
        if not await ping_redis():
            redis_status = "disconnected"
    except Exception:
        redis_status = "disconnected"

    models_loaded = False
    try:
        bundle = get_model_bundle()
        models_loaded = bundle is not None
    except Exception:
        models_loaded = False

    return HealthResponse(
        status="ok",
        database=db_status,
        redis=redis_status,
        models_loaded=models_loaded,
    )
