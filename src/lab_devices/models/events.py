from datetime import datetime

from pydantic import BaseModel, Field


class StateRecord(BaseModel):
    name: str
    params: dict[str, float | str] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=datetime.now)
    ended_at: datetime | None = None


class InstantEvent(BaseModel):
    name: str
    params: dict[str, float | str] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
