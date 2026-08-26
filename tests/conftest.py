import pytest

@pytest.fixture(autouse=True)
def reset_redis_singleton():
    """
    Ensure the Redis singleton is cleared before and after each test.
    This prevents aioredis ConnectionPool instances from being bound to
    closed event loops from prior test modules (e.g. test_api_detect.py's TestClient
    which calls close_redis on application shutdown).
    We clear the reference directly to avoid pytest-asyncio fixture teardown issues.
    """
    import db.redis_client
    import detection.model_loader
    db.redis_client._redis_client = None
    detection.model_loader._model_bundle = None
    yield
    db.redis_client._redis_client = None
    detection.model_loader._model_bundle = None
