from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError

from data.dto import (
    AuthTokenResponse,
    FollowRequestPublic,
    RegisterRequest,
    ShareRequest,
    SpotPublic,
    SpotUpsertRequest,
    SupportTicketPublic,
    SupportTicketRequest,
    UpdateProfileRequest,
    UserPublic,
)
from data.mongo_context import social_db as _social_db, spots_db as _spots_db
from routing.auth_dependency import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET, get_current_user


_index_lock = Lock()
_indexes_ready = False


def _ensure_indexes() -> None:
    global _indexes_ready
    with _index_lock:
        if _indexes_ready:
            return

        social_db = _social_db()
        spots_db = _spots_db()

        social_db["users"].create_index([("username", ASCENDING)], unique=True)
        social_db["users"].create_index([("email", ASCENDING)], unique=True)
        social_db["users"].create_index([("display_name", ASCENDING)])

        social_db["favorites"].create_index([("user_id", ASCENDING), ("spot_id", ASCENDING)], unique=True)
        social_db["follows"].create_index([("follower_id", ASCENDING), ("followee_id", ASCENDING)], unique=True)
        social_db["shares"].create_index([("user_id", ASCENDING), ("spot_id", ASCENDING), ("created_at", ASCENDING)])
        social_db["follow_requests"].create_index([("follower_id", ASCENDING), ("followee_id", ASCENDING)], unique=True)
        social_db["blocks"].create_index([("blocker_id", ASCENDING), ("blocked_id", ASCENDING)], unique=True)
        social_db["support_tickets"].create_index([("user_id", ASCENDING), ("created_at", ASCENDING)])
        social_db["support_tickets"].create_index([("status", ASCENDING), ("created_at", ASCENDING)])

        spots_db["spots"].create_index([("owner_id", ASCENDING)])
        spots_db["spots"].create_index([("visibility", ASCENDING)])
        spots_db["spots"].create_index([("invite_user_ids", ASCENDING)])

        _indexes_ready = True


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _serialize_id(v: Any) -> str:
    if isinstance(v, ObjectId):
        return str(v)
    return str(v)


def _as_text(value: Any) -> str:
    return str(value or "").strip()


def _as_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _normalized_username(value: Any) -> str:
    return _as_text(value).lower()


def _normalize_social_accounts(value: Any) -> Dict[str, str]:
    if not isinstance(value, dict):
        return {}

    out: Dict[str, str] = {}
    for k, v in value.items():
        key = _as_text(k)
        val = _as_text(v)
        if not key or not val:
            continue
        if len(key) > 40 or len(val) > 500:
            continue
        out[key] = val
    return out


def _normalize_id_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []

    out: List[str] = []
    seen = set()
    for raw in value:
        sid = _as_text(raw)
        if not ObjectId.is_valid(sid):
            continue
        if sid in seen:
            continue
        seen.add(sid)
        out.append(sid)
    return out


def _spot_owner_id(spot_doc: Dict[str, Any]) -> str:
    return _as_text(spot_doc.get("owner_id"))


def _spot_visibility(spot_doc: Dict[str, Any]) -> str:
    visibility = _as_text(spot_doc.get("visibility") or "public").lower()
    if visibility in {"public", "following", "invite_only", "personal"}:
        return visibility
    return "public"


def _is_following(follower_id: str, followee_id: str) -> bool:
    if not follower_id or not followee_id:
        return False
    db = _social_db()
    return db["follows"].count_documents({"follower_id": follower_id, "followee_id": followee_id}, limit=1) > 0


def _is_blocked_pair(user_a: str, user_b: str) -> bool:
    if not user_a or not user_b:
        return False
    db = _social_db()
    return db["blocks"].count_documents(
        {
            "$or": [
                {"blocker_id": user_a, "blocked_id": user_b},
                {"blocker_id": user_b, "blocked_id": user_a},
            ]
        },
        limit=1,
    ) > 0


def _can_view_spot(viewer_id: str, spot_doc: Dict[str, Any]) -> bool:
    owner_id = _spot_owner_id(spot_doc)
    visibility = _spot_visibility(spot_doc)

    if not owner_id:
        return visibility == "public"
    if viewer_id and viewer_id == owner_id:
        return True
    if _is_blocked_pair(viewer_id, owner_id):
        return False

    if visibility == "public":
        return True
    if visibility == "personal":
        return False
    if visibility == "following":
        return _is_following(viewer_id, owner_id)
    if visibility == "invite_only":
        return viewer_id in set(_normalize_id_list(spot_doc.get("invite_user_ids")))
    return False


def _can_view_private_user(target_user: Dict[str, Any], viewer_id: str) -> bool:
    target_id = _serialize_id(target_user.get("_id"))
    if viewer_id == target_id:
        return True
    if _is_blocked_pair(viewer_id, target_id):
        return False
    if not bool(target_user.get("follow_requires_approval", False)):
        return True
    return _is_following(viewer_id, target_id)


def _to_spot_public(doc: Dict[str, Any]) -> SpotPublic:
    return SpotPublic(
        id=_serialize_id(doc.get("_id")),
        owner_id=_spot_owner_id(doc),
        title=_as_text(doc.get("title")),
        description=_as_text(doc.get("description")),
        tags=[_as_text(tag) for tag in doc.get("tags", []) if _as_text(tag)],
        lat=_as_float(doc.get("lat"), 0.0),
        lon=_as_float(doc.get("lon"), 0.0),
        images=[_as_text(img) for img in doc.get("images", []) if _as_text(img)],
        visibility=_spot_visibility(doc),
        invite_user_ids=_normalize_id_list(doc.get("invite_user_ids")),
        created_at=doc.get("created_at") or datetime.now(UTC),
    )


def _to_user_public(doc: Dict[str, Any]) -> UserPublic:
    return UserPublic(
        id=_serialize_id(doc.get("_id")),
        username=_as_text(doc.get("username")),
        email=_as_text(doc.get("email")),
        display_name=_as_text(doc.get("display_name") or doc.get("username")),
        bio=_as_text(doc.get("bio")),
        avatar_image=_as_text(doc.get("avatar_image")),
        social_accounts=_normalize_social_accounts(doc.get("social_accounts")),
        follow_requires_approval=bool(doc.get("follow_requires_approval", False)),
        created_at=doc.get("created_at") or datetime.now(UTC),
    )


def _to_support_ticket_public(doc: Dict[str, Any]) -> SupportTicketPublic:
    category = _as_text(doc.get("category")).lower()
    if category not in {"bug", "feature", "complaint", "question", "other"}:
        category = "other"

    status_text = _as_text(doc.get("status")).lower()
    status_value = "open" if status_text != "closed" else "closed"

    return SupportTicketPublic(
        id=_serialize_id(doc.get("_id")),
        user_id=_as_text(doc.get("user_id")),
        category=category,
        subject=_as_text(doc.get("subject")),
        message=_as_text(doc.get("message")),
        page=_as_text(doc.get("page")),
        contact_email=_as_text(doc.get("contact_email")),
        allow_contact=bool(doc.get("allow_contact", False)),
        status=status_value,
        created_at=doc.get("created_at") or datetime.now(UTC),
    )


def _safe_user_projection() -> Dict[str, int]:
    return {
        "username": 1,
        "email": 1,
        "display_name": 1,
        "bio": 1,
        "avatar_image": 1,
        "social_accounts": 1,
        "follow_requires_approval": 1,
        "created_at": 1,
    }


def _hash_password(password: str) -> str:
    return pwd_context.hash(password)


def _verify_password(password: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(password, password_hash)
    except Exception:
        return False


def _create_access_token(user_id: str, username: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "username": username,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_EXPIRE_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _parse_object_id(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID format")
    return ObjectId(value)


def _viewer_user_id(current_user: Dict[str, Any]) -> str:
    return _serialize_id(current_user.get("_id"))


def _build_spot_doc(payload: SpotUpsertRequest, owner_id: str, created_at: Optional[datetime] = None) -> Dict[str, Any]:
    return {
        "owner_id": owner_id,
        "title": _as_text(payload.title),
        "description": _as_text(payload.description),
        "tags": [_as_text(tag) for tag in payload.tags if _as_text(tag)],
        "lat": _as_float(payload.lat, 0.0),
        "lon": _as_float(payload.lon, 0.0),
        "images": [_as_text(img) for img in payload.images if _as_text(img)],
        "visibility": payload.visibility,
        "invite_user_ids": _normalize_id_list(payload.invite_user_ids),
        "created_at": created_at or datetime.now(UTC),
    }


auth_router = APIRouter(prefix="/auth", tags=["Auth"])
social_router = APIRouter(prefix="/social", tags=["Social"])


@auth_router.on_event("startup")
def _startup_indexes() -> None:
    _ensure_indexes()


@auth_router.post("/register", response_model=AuthTokenResponse)
def register(req: RegisterRequest):
    _ensure_indexes()
    db = _social_db()

    username = _normalized_username(req.username)
    email = _normalized_username(req.email)
    if not username or not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username and email are required")

    doc = {
        "username": username,
        "email": email,
        "password_hash": _hash_password(req.password),
        "display_name": _as_text(req.display_name) or username,
        "bio": "",
        "avatar_image": "",
        "social_accounts": {},
        "follow_requires_approval": False,
        "created_at": datetime.now(UTC),
    }

    try:
        result = db["users"].insert_one(doc)
    except DuplicateKeyError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username or email already exists") from e

    user_doc = db["users"].find_one({"_id": result.inserted_id})
    if not user_doc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User creation failed")

    token = _create_access_token(str(user_doc["_id"]), user_doc["username"])
    return AuthTokenResponse(access_token=token, user=_to_user_public(user_doc))


@auth_router.post("/login", response_model=AuthTokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    _ensure_indexes()
    db = _social_db()

    login_name = _normalized_username(form_data.username)
    doc = db["users"].find_one({"$or": [{"username": login_name}, {"email": login_name}]})
    if not doc or not _verify_password(form_data.password or "", _as_text(doc.get("password_hash"))):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username/email or password")

    token = _create_access_token(str(doc["_id"]), _as_text(doc.get("username")))
    return AuthTokenResponse(access_token=token, user=_to_user_public(doc))


@social_router.get("/me", response_model=UserPublic)
def me(current_user: Dict[str, Any] = Depends(get_current_user)):
    return _to_user_public(current_user)


@social_router.put("/me", response_model=UserPublic)
def update_me(req: UpdateProfileRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    _ensure_indexes()
    db = _social_db()

    updates: Dict[str, Any] = {}

    if req.username is not None:
        username = _normalized_username(req.username)
        if not re.fullmatch(r"[a-z0-9_.-]{3,40}", username):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid username format")
        updates["username"] = username

    if req.email is not None:
        email = _normalized_username(req.email)
        if "@" not in email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format")
        updates["email"] = email

    if req.display_name is not None:
        updates["display_name"] = _as_text(req.display_name)

    if req.bio is not None:
        updates["bio"] = _as_text(req.bio)

    if req.avatar_image is not None:
        updates["avatar_image"] = _as_text(req.avatar_image)

    if req.social_accounts is not None:
        updates["social_accounts"] = _normalize_social_accounts(req.social_accounts)

    if req.follow_requires_approval is not None:
        updates["follow_requires_approval"] = bool(req.follow_requires_approval)

    if req.new_password is not None:
        current_password = _as_text(req.current_password)
        if not current_password:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is required")

        current_hash = _as_text(current_user.get("password_hash"))
        if not _verify_password(current_password, current_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")
        updates["password_hash"] = _hash_password(req.new_password)

    if not updates:
        return _to_user_public(current_user)

    try:
        db["users"].update_one({"_id": current_user["_id"]}, {"$set": updates})
    except DuplicateKeyError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username or email already exists") from e

    updated = db["users"].find_one({"_id": current_user["_id"]})
    if not updated:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Profile update failed")
    return _to_user_public(updated)


@social_router.get("/users/search", response_model=List[UserPublic])
def search_users(
    q: str = Query(default="", max_length=80),
    limit: int = Query(default=20, ge=1, le=50),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    db = _social_db()
    me_id = _viewer_user_id(current_user)
    query = _as_text(q)
    if not query:
        return []
    regex = re.compile(re.escape(query), re.IGNORECASE)

    users = list(
        db["users"].find(
            {"$or": [{"username": regex}, {"display_name": regex}]},
            _safe_user_projection(),
        ).limit(limit)
    )

    out: List[UserPublic] = []
    for user_doc in users:
        user_id = _serialize_id(user_doc.get("_id"))
        if user_id != me_id and _is_blocked_pair(me_id, user_id):
            continue
        out.append(_to_user_public(user_doc))
    return out


@social_router.get("/users/{user_id}/profile", response_model=UserPublic)
def user_profile(user_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = _social_db()
    target_oid = _parse_object_id(user_id)
    target = db["users"].find_one({"_id": target_oid}, _safe_user_projection())
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    me_id = _viewer_user_id(current_user)
    target_id = _serialize_id(target.get("_id"))
    if me_id != target_id and _is_blocked_pair(me_id, target_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return _to_user_public(target)


@social_router.get("/spots", response_model=List[SpotPublic])
def list_visible_spots(current_user: Dict[str, Any] = Depends(get_current_user)):
    db = _spots_db()
    me_id = _viewer_user_id(current_user)
    docs = list(db["spots"].find({}).sort("created_at", -1).limit(1500))
    return [_to_spot_public(doc) for doc in docs if _can_view_spot(me_id, doc)]


@social_router.post("/spots", response_model=SpotPublic)
def create_spot(req: SpotUpsertRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = _spots_db()
    me_id = _viewer_user_id(current_user)
    doc = _build_spot_doc(req, owner_id=me_id)
    result = db["spots"].insert_one(doc)
    created = db["spots"].find_one({"_id": result.inserted_id})
    if not created:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Spot creation failed")
    return _to_spot_public(created)


@social_router.put("/spots/{spot_id}", response_model=SpotPublic)
def update_spot(spot_id: str, req: SpotUpsertRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = _spots_db()
    oid = _parse_object_id(spot_id)
    existing = db["spots"].find_one({"_id": oid})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spot not found")

    me_id = _viewer_user_id(current_user)
    owner_id = _spot_owner_id(existing)
    if owner_id and owner_id != me_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can edit this spot")

    next_doc = _build_spot_doc(req, owner_id=owner_id or me_id, created_at=existing.get("created_at"))
    db["spots"].update_one({"_id": oid}, {"$set": next_doc})
    updated = db["spots"].find_one({"_id": oid})
    if not updated:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Spot update failed")
    return _to_spot_public(updated)


@social_router.delete("/spots/{spot_id}")
def delete_spot(spot_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = _spots_db()
    oid = _parse_object_id(spot_id)
    existing = db["spots"].find_one({"_id": oid})
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spot not found")

    me_id = _viewer_user_id(current_user)
    owner_id = _spot_owner_id(existing)
    if owner_id and owner_id != me_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can delete this spot")

    db["spots"].delete_one({"_id": oid})
    social_db = _social_db()
    social_db["favorites"].delete_many({"spot_id": spot_id})
    social_db["shares"].delete_many({"spot_id": spot_id})
    return {"ok": True}


@social_router.get("/users/{user_id}/spots", response_model=List[SpotPublic])
def user_spots(user_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = _social_db()
    target_oid = _parse_object_id(user_id)
    target = db["users"].find_one({"_id": target_oid}, _safe_user_projection())
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    me_id = _viewer_user_id(current_user)
    target_id = _serialize_id(target_oid)
    if me_id != target_id and _is_blocked_pair(me_id, target_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    spots_db = _spots_db()
    docs = list(spots_db["spots"].find({"owner_id": target_id}).sort("created_at", -1).limit(1200))
    return [_to_spot_public(doc) for doc in docs if _can_view_spot(me_id, doc)]


@social_router.post("/favorites/{spot_id}")
def add_favorite(spot_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    spots_db = _spots_db()
    spot = spots_db["spots"].find_one({"_id": _parse_object_id(spot_id)})
    if not spot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spot not found")

    me_id = _viewer_user_id(current_user)
    if not _can_view_spot(me_id, spot):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Spot is not visible to you")

    db = _social_db()
    doc = {"user_id": me_id, "spot_id": spot_id, "created_at": datetime.now(UTC)}
    try:
        db["favorites"].insert_one(doc)
    except DuplicateKeyError:
        pass
    return {"ok": True}


@social_router.delete("/favorites/{spot_id}")
def remove_favorite(spot_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = _social_db()
    db["favorites"].delete_one({"user_id": _viewer_user_id(current_user), "spot_id": spot_id})
    return {"ok": True}


@social_router.get("/favorites", response_model=List[SpotPublic])
def list_favorites(current_user: Dict[str, Any] = Depends(get_current_user)):
    social_db = _social_db()
    spots_db = _spots_db()
    me_id = _viewer_user_id(current_user)

    rows = list(social_db["favorites"].find({"user_id": me_id}, {"spot_id": 1, "_id": 0}))
    spot_ids = [r.get("spot_id") for r in rows if isinstance(r.get("spot_id"), str) and ObjectId.is_valid(r.get("spot_id"))]
    oids = [_parse_object_id(sid) for sid in spot_ids]
    spots = list(spots_db["spots"].find({"_id": {"$in": oids}})) if oids else []
    return [_to_spot_public(doc) for doc in spots if _can_view_spot(me_id, doc)]


@social_router.get("/users/{user_id}/favorites", response_model=List[SpotPublic])
def user_favorites(user_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    social_db = _social_db()
    spots_db = _spots_db()
    target_oid = _parse_object_id(user_id)
    target = social_db["users"].find_one({"_id": target_oid}, _safe_user_projection())
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    me_id = _viewer_user_id(current_user)
    if not _can_view_private_user(target, me_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User profile is private")

    target_id = _serialize_id(target_oid)
    rows = list(social_db["favorites"].find({"user_id": target_id}, {"spot_id": 1, "_id": 0}))
    spot_ids = [r.get("spot_id") for r in rows if isinstance(r.get("spot_id"), str) and ObjectId.is_valid(r.get("spot_id"))]
    oids = [_parse_object_id(sid) for sid in spot_ids]
    spots = list(spots_db["spots"].find({"_id": {"$in": oids}})) if oids else []
    return [_to_spot_public(doc) for doc in spots if _can_view_spot(me_id, doc)]


@social_router.get("/follow/requests", response_model=List[FollowRequestPublic])
def follow_requests(current_user: Dict[str, Any] = Depends(get_current_user)):
    db = _social_db()
    me_id = _viewer_user_id(current_user)
    rows = list(db["follow_requests"].find({"followee_id": me_id}).sort("created_at", -1).limit(500))

    out: List[FollowRequestPublic] = []
    for row in rows:
        follower_id = _as_text(row.get("follower_id"))
        if not ObjectId.is_valid(follower_id):
            continue
        follower = db["users"].find_one({"_id": _parse_object_id(follower_id)}, _safe_user_projection())
        if not follower:
            continue
        out.append(
            FollowRequestPublic(
                follower=_to_user_public(follower),
                created_at=row.get("created_at") or datetime.now(UTC),
            )
        )
    return out


@social_router.post("/follow/requests/{follower_id}/approve")
def approve_follow_request(follower_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = _social_db()
    follower_sid = _serialize_id(_parse_object_id(follower_id))
    me_id = _viewer_user_id(current_user)

    req_row = db["follow_requests"].find_one({"follower_id": follower_sid, "followee_id": me_id})
    if not req_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow request not found")

    try:
        db["follows"].insert_one(
            {
                "follower_id": follower_sid,
                "followee_id": me_id,
                "created_at": datetime.now(UTC),
            }
        )
    except DuplicateKeyError:
        pass
    db["follow_requests"].delete_one({"follower_id": follower_sid, "followee_id": me_id})
    return {"ok": True}


@social_router.post("/follow/requests/{follower_id}/reject")
def reject_follow_request(follower_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = _social_db()
    follower_sid = _serialize_id(_parse_object_id(follower_id))
    me_id = _viewer_user_id(current_user)
    db["follow_requests"].delete_one({"follower_id": follower_sid, "followee_id": me_id})
    return {"ok": True}


@social_router.post("/follow/{user_id}")
def follow_user(user_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    target_oid = _parse_object_id(user_id)
    target_id = _serialize_id(target_oid)
    me_id = _viewer_user_id(current_user)
    if me_id == target_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot follow yourself")

    db = _social_db()
    target_user = db["users"].find_one({"_id": target_oid}, _safe_user_projection())
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if _is_blocked_pair(me_id, target_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot follow this user")

    if _is_following(me_id, target_id):
        return {"ok": True, "status": "following"}

    if bool(target_user.get("follow_requires_approval", False)):
        db["follow_requests"].update_one(
            {"follower_id": me_id, "followee_id": target_id},
            {"$set": {"created_at": datetime.now(UTC)}},
            upsert=True,
        )
        return {"ok": True, "status": "pending"}

    try:
        db["follows"].insert_one(
            {
                "follower_id": me_id,
                "followee_id": target_id,
                "created_at": datetime.now(UTC),
            }
        )
    except DuplicateKeyError:
        pass

    db["follow_requests"].delete_one({"follower_id": me_id, "followee_id": target_id})
    return {"ok": True, "status": "following"}


@social_router.delete("/follow/{user_id}")
def unfollow_user(user_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = _social_db()
    me_id = _viewer_user_id(current_user)
    target_id = _serialize_id(_parse_object_id(user_id))
    db["follows"].delete_one({"follower_id": me_id, "followee_id": target_id})
    db["follow_requests"].delete_one({"follower_id": me_id, "followee_id": target_id})
    return {"ok": True}


@social_router.get("/followers/{user_id}", response_model=List[UserPublic])
def followers(user_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = _social_db()
    target_oid = _parse_object_id(user_id)
    target_user = db["users"].find_one({"_id": target_oid}, _safe_user_projection())
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    me_id = _viewer_user_id(current_user)
    if not _can_view_private_user(target_user, me_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User profile is private")

    target_id = _serialize_id(target_oid)
    rows = list(db["follows"].find({"followee_id": target_id}))
    follower_ids = [r.get("follower_id") for r in rows if isinstance(r.get("follower_id"), str)]
    oids = [_parse_object_id(uid) for uid in follower_ids if ObjectId.is_valid(uid)]
    users = list(db["users"].find({"_id": {"$in": oids}}, _safe_user_projection())) if oids else []
    return [_to_user_public(u) for u in users if not _is_blocked_pair(me_id, _serialize_id(u.get("_id")))]


@social_router.get("/following/{user_id}", response_model=List[UserPublic])
def following(user_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = _social_db()
    target_oid = _parse_object_id(user_id)
    target_user = db["users"].find_one({"_id": target_oid}, _safe_user_projection())
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    me_id = _viewer_user_id(current_user)
    if not _can_view_private_user(target_user, me_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User profile is private")

    target_id = _serialize_id(target_oid)
    rows = list(db["follows"].find({"follower_id": target_id}))
    followee_ids = [r.get("followee_id") for r in rows if isinstance(r.get("followee_id"), str)]
    oids = [_parse_object_id(uid) for uid in followee_ids if ObjectId.is_valid(uid)]
    users = list(db["users"].find({"_id": {"$in": oids}}, _safe_user_projection())) if oids else []
    return [_to_user_public(u) for u in users if not _is_blocked_pair(me_id, _serialize_id(u.get("_id")))]


@social_router.delete("/followers/{user_id}")
def remove_follower(user_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = _social_db()
    me_id = _viewer_user_id(current_user)
    follower_id = _serialize_id(_parse_object_id(user_id))
    db["follows"].delete_one({"follower_id": follower_id, "followee_id": me_id})
    db["follow_requests"].delete_one({"follower_id": follower_id, "followee_id": me_id})
    return {"ok": True}


@social_router.post("/block/{user_id}")
def block_user(user_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = _social_db()
    me_id = _viewer_user_id(current_user)
    target_id = _serialize_id(_parse_object_id(user_id))
    if me_id == target_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot block yourself")

    db["blocks"].update_one(
        {"blocker_id": me_id, "blocked_id": target_id},
        {"$set": {"created_at": datetime.now(UTC)}},
        upsert=True,
    )

    db["follows"].delete_many(
        {
            "$or": [
                {"follower_id": me_id, "followee_id": target_id},
                {"follower_id": target_id, "followee_id": me_id},
            ]
        }
    )
    db["follow_requests"].delete_many(
        {
            "$or": [
                {"follower_id": me_id, "followee_id": target_id},
                {"follower_id": target_id, "followee_id": me_id},
            ]
        }
    )
    return {"ok": True}


@social_router.delete("/block/{user_id}")
def unblock_user(user_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = _social_db()
    me_id = _viewer_user_id(current_user)
    target_id = _serialize_id(_parse_object_id(user_id))
    db["blocks"].delete_one({"blocker_id": me_id, "blocked_id": target_id})
    return {"ok": True}


@social_router.get("/blocked", response_model=List[UserPublic])
def blocked_users(current_user: Dict[str, Any] = Depends(get_current_user)):
    db = _social_db()
    me_id = _viewer_user_id(current_user)
    rows = list(db["blocks"].find({"blocker_id": me_id}).limit(500))
    ids = [r.get("blocked_id") for r in rows if isinstance(r.get("blocked_id"), str)]
    oids = [_parse_object_id(uid) for uid in ids if ObjectId.is_valid(uid)]
    users = list(db["users"].find({"_id": {"$in": oids}}, _safe_user_projection())) if oids else []
    return [_to_user_public(u) for u in users]


@social_router.post("/share/{spot_id}")
def share_spot(spot_id: str, req: ShareRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    spots_db = _spots_db()
    spot = spots_db["spots"].find_one({"_id": _parse_object_id(spot_id)})
    if not spot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spot not found")

    me_id = _viewer_user_id(current_user)
    if not _can_view_spot(me_id, spot):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Spot is not visible to you")

    db = _social_db()
    db["shares"].insert_one(
        {
            "user_id": me_id,
            "spot_id": spot_id,
            "message": req.message,
            "created_at": datetime.now(UTC),
        }
    )
    return {"ok": True}


@social_router.post("/support/tickets", response_model=SupportTicketPublic, status_code=status.HTTP_201_CREATED)
def create_support_ticket(req: SupportTicketRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = _social_db()
    me_id = _viewer_user_id(current_user)

    contact_email = _as_text(req.contact_email or current_user.get("email"))
    if contact_email and "@" not in contact_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid contact email format")

    now = datetime.now(UTC)
    doc = {
        "user_id": me_id,
        "category": req.category,
        "subject": _as_text(req.subject),
        "message": _as_text(req.message),
        "page": _as_text(req.page),
        "contact_email": contact_email,
        "allow_contact": bool(req.allow_contact),
        "status": "open",
        "created_at": now,
        "updated_at": now,
    }

    created = db["support_tickets"]
    result = created.insert_one(doc)
    row = created.find_one({"_id": result.inserted_id})
    if not row:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Support ticket creation failed")
    return _to_support_ticket_public(row)


@social_router.get("/shared/{user_id}")
def shared(user_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    db = _social_db()
    me_id = _viewer_user_id(current_user)
    target_doc = db["users"].find_one({"_id": _parse_object_id(user_id)}, _safe_user_projection())
    if not target_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not _can_view_private_user(target_doc, me_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User profile is private")

    target_id = _serialize_id(target_doc.get("_id"))
    rows = list(db["shares"].find({"user_id": target_id}).sort("created_at", -1).limit(200))
    out: List[Dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "id": _serialize_id(row.get("_id")),
                "user_id": _as_text(row.get("user_id")),
                "spot_id": _as_text(row.get("spot_id")),
                "message": _as_text(row.get("message")),
                "created_at": row.get("created_at"),
            }
        )
    return out


def get_auth_router() -> APIRouter:
    return auth_router


def get_social_router() -> APIRouter:
    return social_router
