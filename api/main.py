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
from api.schemas import HealthResponse

load_dotenv()


def get_allowed_origins() -> List[str]:
    """Parse ALLOWED_ORIGINS from environment, ensuring no wildcard is used."""
    raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    # Filter out wildcard '*' to strictly protect credentials and dashboard integrity
    filtered_origins = [o for o in origins if o != "*"]
    return filtered_origins if filtered_origins else ["http://localhost:3000"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler:
    - Startup:
      1. Pre-loads both tuned ML models into memory once.
      2. Verifies PostgreSQL database connectivity (SELECT 1).
         (Note: Schema creation is strictly managed by Alembic, not create_all).
      3. Verifies Redis connectivity via ping.
    - Shutdown:
      1. Closes Redis connection pool.
      2. Disposes database engine pool.
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

    yield

    # Shutdown
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
