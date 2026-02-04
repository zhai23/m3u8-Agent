from __future__ import annotations

from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field


TaskStatus = Literal["pending", "running", "paused", "completed", "failed"]


class Task(BaseModel):
    id: str
    url: str
    name: str
    status: TaskStatus = "pending"
    progress: float = 0.0
    speed: Optional[str] = None
    eta: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None



class TaskCreateRequest(BaseModel):
    url: str = Field(min_length=1)
    name: str = Field(min_length=1)
