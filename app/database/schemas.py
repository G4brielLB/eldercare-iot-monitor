from pydantic import BaseModel
from typing import Any, Dict

class HealthMessageSchema(BaseModel):
    id: str
    patient_id: str
    message_type: str
    timestamp: str
    data: Dict[str, Any]

    class Config:
        orm_mode = True
