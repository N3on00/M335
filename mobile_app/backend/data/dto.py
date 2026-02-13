from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

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


@mongo_entity(collection="client_error_reports", tags=["ClientErrors"], prefix="/client-errors")
class ClientErrorReport(BaseModel):
    kind: str = Field(default="exception", max_length=40)
    source: str = Field(default="app", max_length=80)
    message: str = Field(default="", max_length=8000)
    exception_type: Optional[str] = Field(default=None, max_length=200)
    stacktrace: str = Field(default="", max_length=200000)
    context: Dict[str, Any] = Field(default_factory=dict)
    platform: Optional[str] = Field(default=None, max_length=200)
    python_version: Optional[str] = Field(default=None, max_length=200)
    created_at: Optional[datetime] = None

    @field_validator("created_at")
    @classmethod
    def default_now_report(cls, v):
        return v or datetime.now()
