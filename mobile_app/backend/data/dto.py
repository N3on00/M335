from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from routing.registry import mongo_entity


@mongo_entity(collection="spots", tags=["Spots"], prefix="/spots")
class Spot(BaseModel):
    title: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=2000)
    tags: List[str] = Field(default_factory=list)

    lat: float
    lon: float

    # Store images as base64 strings (later you can switch to URLs)
    images: List[str] = Field(default_factory=list)

    created_at: Optional[datetime] = None

    @field_validator("created_at")
    @classmethod
    def default_now(cls, v):
        return v or datetime.now()