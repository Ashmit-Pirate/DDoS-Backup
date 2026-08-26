from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Config
from api.schemas import RuntimeSystemConfig

router = APIRouter(prefix="/api/v1", tags=["Config"])

def get_default_config() -> RuntimeSystemConfig:
    return RuntimeSystemConfig(
        targetApplication="Demo App",
        environment="production",
        mitigationMode="Simulation Only",
        telemetryRefreshRateMs=1000,
        serverAvailability=100,
        baselineRequestRate=1000,
        baselineEntropy=5
    )

@router.get("/config", response_model=RuntimeSystemConfig)
async def get_config(db: Session = Depends(get_db)):
    records = db.query(Config).all()
    config_dict = get_default_config().model_dump()
    
    for r in records:
        if r.key in config_dict:
            # Type cast appropriately
            if isinstance(config_dict[r.key], int):
                try:
                    config_dict[r.key] = int(r.value)
                except ValueError:
                    pass
            else:
                config_dict[r.key] = r.value
                
    return RuntimeSystemConfig(**config_dict)

@router.put("/config", response_model=RuntimeSystemConfig)
async def update_config(config: RuntimeSystemConfig, db: Session = Depends(get_db)):
    config_dict = config.model_dump()
    for k, v in config_dict.items():
        record = db.query(Config).filter(Config.key == k).first()
        if record:
            record.value = str(v)
        else:
            new_record = Config(key=k, value=str(v))
            db.add(new_record)
    db.commit()
    return config
