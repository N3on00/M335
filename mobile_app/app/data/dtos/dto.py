from __future__ import annotations
from typing import List, Optional
from datetime import datetime
from pydantic import Field, BaseModel

class SpotDTO(BaseModel):
    id: Optional[str] = None

    title: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=2000)

    lat: float
    lon: float

    type: str = Field(default="other", max_length=30)
    tags: List[str] = Field(default_factory=list)

    created_at: Optional[datetime] = None
