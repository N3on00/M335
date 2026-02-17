from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from routing.auth_dependency import get_current_user
from routing.registry import mongo_entity


@mongo_entity(
    collection="spots",
    tags=["Spots"],
    prefix="/spots",
    authenticated=True,
    auth_dependency=get_current_user,
)
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
        return v or datetime.now(UTC)


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
        return v or datetime.now(UTC)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=8, max_length=200)
    display_name: Optional[str] = Field(default=None, max_length=120)


class UpdateProfileRequest(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=40)
    email: Optional[str] = Field(default=None, min_length=5, max_length=200)
    display_name: Optional[str] = Field(default=None, max_length=120)
    bio: Optional[str] = Field(default=None, max_length=1200)
    avatar_image: Optional[str] = Field(default=None, max_length=5_000_000)
    social_accounts: Optional[Dict[str, str]] = Field(default=None)
    follow_requires_approval: Optional[bool] = None
    current_password: Optional[str] = Field(default=None, max_length=200)
    new_password: Optional[str] = Field(default=None, min_length=8, max_length=200)


class UserPublic(BaseModel):
    id: str
    username: str
    email: str
    display_name: str
    bio: str = ""
    avatar_image: str = ""
    social_accounts: Dict[str, str] = Field(default_factory=dict)
    follow_requires_approval: bool = False
    created_at: datetime


class SpotUpsertRequest(BaseModel):
    title: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=2000)
    tags: List[str] = Field(default_factory=list)
    lat: float
    lon: float
    images: List[str] = Field(default_factory=list)
    visibility: Literal["public", "following", "invite_only", "personal"] = "public"
    invite_user_ids: List[str] = Field(default_factory=list)


class SpotPublic(BaseModel):
    id: str
    owner_id: str
    title: str
    description: str
    tags: List[str] = Field(default_factory=list)
    lat: float
    lon: float
    images: List[str] = Field(default_factory=list)
    visibility: Literal["public", "following", "invite_only", "personal"] = "public"
    invite_user_ids: List[str] = Field(default_factory=list)
    created_at: datetime


class ShareRequest(BaseModel):
    message: str = Field(default="", max_length=300)


class SupportTicketRequest(BaseModel):
    category: Literal["bug", "feature", "complaint", "question", "other"] = "other"
    subject: str = Field(min_length=3, max_length=140)
    message: str = Field(min_length=10, max_length=6000)
    page: str = Field(default="", max_length=240)
    contact_email: Optional[str] = Field(default=None, max_length=200)
    allow_contact: bool = False


class SupportTicketPublic(BaseModel):
    id: str
    user_id: str
    category: Literal["bug", "feature", "complaint", "question", "other"] = "other"
    subject: str
    message: str
    page: str = ""
    contact_email: str = ""
    allow_contact: bool = False
    status: Literal["open", "closed"] = "open"
    created_at: datetime


class FollowRequestPublic(BaseModel):
    follower: UserPublic
    created_at: datetime


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
