from pydantic import BaseModel
from typing import Any, Dict

class HealthMessageSchema(BaseModel):
    id: str
    patient_id: str
    message_type: str
    data: Dict[str, Any]
    original_timestamp: str

    class Config:
        orm_mode = True
