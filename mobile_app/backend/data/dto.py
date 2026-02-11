from __future__ import annotations

import re
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from routing.registry import mongo_entity


@mongo_entity(collection="spots", tags=["Spots"])
class Spot(BaseModel):
    """Saved place shown on the map."""

    title: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=2000)

    lat: float
    lon: float

    type: str = Field(default="other", max_length=30)
    tags: List[str] = Field(default_factory=list)

    created_at: Optional[datetime] = None

    @field_validator("created_at")
    @classmethod
    def default_now(cls, v):
        return v or datetime.now()


@mongo_entity(collection="weather", tags=["Weather"])
class Weather(BaseModel):
    """Weather reading."""

    temp: float
    pressure: float
    light: float
    winds: float
    winddir: str = Field(min_length=1, max_length=3)
    rain: float
    humidity: float
    time: Optional[datetime] = None

    @field_validator("time")
    @classmethod
    def default_now(cls, v):
        return v or datetime.now()

    @field_validator("winddir")
    @classmethod
    def uppercase_and_validate(cls, v: str) -> str:
        vv = v.upper()
        if not re.fullmatch(r"[A-Z]{1,3}", vv):
            raise ValueError("winddir must be 1-3 letters (e.g., N, NE, SSW)")
        return vv


@mongo_entity(collection="ossd", tags=["OSSD"])
class OSSD(BaseModel):
    """OSSD Event (without FK)."""

    time: Optional[datetime] = None
    lichtgitterNr: int
    ossdNr: int
    ossdStatus: str

    @field_validator("time")
    @classmethod
    def default_now(cls, v):
        return v or datetime.now()
