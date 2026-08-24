from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class AskRequest(BaseModel):
    question: str
    admin_user_id: Optional[str] = "USR-DEV"
    session_id: Optional[str] = None   # omit to start a new session
    model_mode: Optional[str] = "auto" # "auto", "groq", "local"
    history: Optional[list[dict]] = None


class ToolCallTrace(BaseModel):
    tool_name: str
    query_summary: str
    rows_returned: int

class AskResponse(BaseModel):
    session_id: str
    answer: str
    tool_calls: list[ToolCallTrace] = Field(default_factory=list)
    model_used: Optional[str] = None

class SensorReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reading_id: str
    sensor_id: str
    captured_at: str
    value: float
    unit: str
    alert_level: str

class AIEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ai_event_id: str
    detected_at: str
    event_type: str
    camera_id: str
    zone_id: str
    severity: str
    status: str

