from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class AskRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User question or instruction (max 2000 characters)"
    )
    admin_user_id: Optional[str] = Field(
        default="USR-DEV",
        max_length=64,
        pattern=r"^[a-zA-Z0-9_\-\.]+$",
        description="Actor or user ID"
    )
    user_role: Optional[str] = Field(
        default="HSE_MANAGER",
        max_length=64,
        pattern=r"^[a-zA-Z0-9_\-\.]+$",
        description="User RBAC role"
    )
    session_id: Optional[str] = Field(
        default=None,
        max_length=64,
        pattern=r"^[a-zA-Z0-9_\-\.]+$",
        description="Session identifier"
    )
    model_mode: Optional[str] = Field(
        default="auto",
        max_length=32,
        description="Model execution mode (auto, groq, local)"
    )
    history: Optional[list[dict]] = Field(
        default=None,
        max_length=10,
        description="Recent message history (max 10 items)"
    )

    @field_validator("history")
    @classmethod
    def validate_history_size(cls, v: Optional[list[dict]]) -> Optional[list[dict]]:
        if v is not None:
            total_chars = sum(len(str(item.get("content") or item.get("text") or "")) for item in v if isinstance(item, dict))
            if total_chars > 10000:
                raise ValueError("Total conversation history length exceeds 10,000 characters limit.")
        return v


class ToolCallTrace(BaseModel):
    tool_name: str
    query_summary: str
    rows_returned: int
    args: Optional[dict] = None
    result: Optional[dict] = None


class AskResponse(BaseModel):
    session_id: str
    answer: str
    tool_calls: list[ToolCallTrace] = Field(default_factory=list)
    model_used: Optional[str] = None
    user_role: Optional[str] = None


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
