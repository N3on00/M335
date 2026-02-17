from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime
import os
import re
from threading import Lock
from typing import Any

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError

from data.dto import (
    BlockRef,
    FavoriteRef,
    FollowRef,
    FollowRequestRef,
    ShareRequest,
    SpotPublic,
    SpotUpsertRequest,
    SupportTicketPublic,
    SupportTicketRequest,
    UpdateProfileRequest,
    UserPublic,
)
from data.mongo_repository import MongoRepository
from routing.auth_routes import get_auth_user_repository, get_current_user, password_extension


class _SocialRepositories:
    def __init__(self) -> None:
        self.users = get_auth_user_repository()
        self.spots = MongoRepository(
            collection_name="spots",
            model_type=SpotUpsertRequest,
            db_name=_spots_db_name(),
        )
        self.favorites = MongoRepository(
            collection_name="favorites",
            model_type=FavoriteRef,
            db_name=_social_db_name(),
        )
        self.follows = MongoRepository(
            collection_name="follows",
            model_type=FollowRef,
            db_name=_social_db_name(),
        )
        self.follow_requests = MongoRepository(
            collection_name="follow_requests",
            model_type=FollowRequestRef,
            db_name=_social_db_name(),
        )
        self.blocks = MongoRepository(
            collection_name="blocks",
            model_type=BlockRef,
            db_name=_social_db_name(),
        )
        self.shares = MongoRepository(
            collection_name="shares",
            model_type=ShareRequest,
            db_name=_social_db_name(),
        )
        self.support_tickets = MongoRepository(
            collection_name="support_tickets",
            model_type=SupportTicketRequest,
            db_name=_social_db_name(),
        )


_SOCIAL_REPOS: _SocialRepositories | None = None
_SOCIAL_ROUTER: APIRouter | None = None
_INDEX_LOCK = Lock()
_INDEXES_READY = False


def _social_db_name() -> str:
    return str(os.getenv("MONGO_AUTH_DB") or "SpotOnSightAuth").strip() or "SpotOnSightAuth"


def _spots_db_name() -> str:
    return str(os.getenv("MONGO_SPOTS_DB") or "spot_on_sight").strip() or "spot_on_sight"


def _repos() -> _SocialRepositories:
    global _SOCIAL_REPOS
    if _SOCIAL_REPOS is None:
        _SOCIAL_REPOS = _SocialRepositories()
    return _SOCIAL_REPOS


def _ensure_indexes() -> None:
    global _INDEXES_READY
    if _INDEXES_READY:
        return

    with _INDEX_LOCK:
        if _INDEXES_READY:
            return

        repos = _repos()
        repos.favorites.collection.create_index([("user_id", ASCENDING), ("spot_id", ASCENDING)], unique=True)
        repos.follows.collection.create_index([("follower_id", ASCENDING), ("followee_id", ASCENDING)], unique=True)
        repos.follow_requests.collection.create_index(
            [("follower_id", ASCENDING), ("followee_id", ASCENDING)],
            unique=True,
        )
        repos.blocks.collection.create_index([("blocker_id", ASCENDING), ("blocked_id", ASCENDING)], unique=True)
        repos.shares.collection.create_index([("user_id", ASCENDING), ("spot_id", ASCENDING), ("created_at", ASCENDING)])
        repos.support_tickets.collection.create_index([("user_id", ASCENDING), ("created_at", ASCENDING)])
        repos.support_tickets.collection.create_index([("status", ASCENDING), ("created_at", ASCENDING)])

        repos.spots.collection.create_index([("owner_id", ASCENDING)])
        repos.spots.collection.create_index([("visibility", ASCENDING)])
        repos.spots.collection.create_index([("invite_user_ids", ASCENDING)])

        _INDEXES_READY = True


@asynccontextmanager
async def _social_lifespan(_app):
    _ensure_indexes()
    yield


def _serialize_id(value: Any) -> str:
    if isinstance(value, ObjectId):
        return str(value)
    return str(value or "")


def _as_text(value: Any) -> str:
    return str(value or "").strip()


def _as_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _normalize_login(value: Any) -> str:
    return _as_text(value).lower()


def _normalize_social_accounts(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}

    out: dict[str, str] = {}
    for key, item in value.items():
        k = _as_text(key)
        v = _as_text(item)
        if not k or not v:
            continue
        if len(k) > 40 or len(v) > 500:
            continue
        out[k] = v
    return out


def _normalize_id_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    out: list[str] = []
    seen: set[str] = set()
    for raw in value:
        sid = _as_text(raw)
        if not ObjectId.is_valid(sid):
            continue
        if sid in seen:
            continue
        seen.add(sid)
        out.append(sid)
    return out


def _spot_owner_id(spot_doc: dict[str, Any]) -> str:
    return _as_text(spot_doc.get("owner_id"))


def _spot_visibility(spot_doc: dict[str, Any]) -> str:
    visibility = _as_text(spot_doc.get("visibility") or "public").lower()
    if visibility in {"public", "following", "invite_only", "personal"}:
        return visibility
    return "public"


def _safe_user_projection() -> dict[str, int]:
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


def _parse_object_id(value: str) -> ObjectId:
    text = _as_text(value)
    if not ObjectId.is_valid(text):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID format")
    return ObjectId(text)


def _spot_lookup_query(spot_id: str) -> dict[str, Any]:
    text = _as_text(spot_id)
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID format")
    if ObjectId.is_valid(text):
        oid = ObjectId(text)
        return {"$or": [{"_id": oid}, {"_id": text}]}
    return {"_id": text}


def _spot_document_by_id(repos: _SocialRepositories, spot_id: str) -> dict[str, Any] | None:
    return repos.spots.find_one(_spot_lookup_query(spot_id))


def _viewer_user_id(current_user: dict[str, Any]) -> str:
    return _serialize_id(current_user.get("_id"))


def _is_following(repos: _SocialRepositories, follower_id: str, followee_id: str) -> bool:
    if not follower_id or not followee_id:
        return False
    return repos.follows.count_documents(
        {"follower_id": follower_id, "followee_id": followee_id},
        limit=1,
    ) > 0


def _is_blocked_pair(repos: _SocialRepositories, user_a: str, user_b: str) -> bool:
    if not user_a or not user_b:
        return False
    return repos.blocks.count_documents(
        {
            "$or": [
                {"blocker_id": user_a, "blocked_id": user_b},
                {"blocker_id": user_b, "blocked_id": user_a},
            ]
        },
        limit=1,
    ) > 0


def _can_view_spot(repos: _SocialRepositories, viewer_id: str, spot_doc: dict[str, Any]) -> bool:
    owner_id = _spot_owner_id(spot_doc)
    visibility = _spot_visibility(spot_doc)

    if not owner_id:
        return visibility == "public"
    if viewer_id and viewer_id == owner_id:
        return True
    if viewer_id and _is_blocked_pair(repos, viewer_id, owner_id):
        return False

    if visibility == "public":
        return True
    if visibility == "personal":
        return False
    if visibility == "following":
        return _is_following(repos, viewer_id, owner_id)
    if visibility == "invite_only":
        return viewer_id in set(_normalize_id_list(spot_doc.get("invite_user_ids")))
    return False


def _can_view_private_user(repos: _SocialRepositories, target_user: dict[str, Any], viewer_id: str) -> bool:
    target_id = _serialize_id(target_user.get("_id"))
    if viewer_id == target_id:
        return True
    if _is_blocked_pair(repos, viewer_id, target_id):
        return False
    if not bool(target_user.get("follow_requires_approval", False)):
        return True
    return _is_following(repos, viewer_id, target_id)


def _to_user_public(doc: dict[str, Any]) -> UserPublic:
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


def _to_spot_public(doc: dict[str, Any]) -> SpotPublic:
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


def _to_support_ticket_public(doc: dict[str, Any]) -> SupportTicketPublic:
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


def _build_spot_doc(payload: SpotUpsertRequest, owner_id: str, created_at: datetime | None = None) -> dict[str, Any]:
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


def _visible_favorite_refs(
    repos: _SocialRepositories,
    rows: list[dict[str, Any]],
    viewer_user_id: str,
) -> list[FavoriteRef]:
    spot_ids = [_as_text(row.get("spot_id")) for row in rows]
    unique_spot_ids = list(dict.fromkeys([sid for sid in spot_ids if sid]))
    if not unique_spot_ids:
        return []

    lookup_ids: list[Any] = []
    for sid in unique_spot_ids:
        lookup_ids.append(sid)
        if ObjectId.is_valid(sid):
            lookup_ids.append(ObjectId(sid))

    spot_docs = list(
        repos.spots.collection.find(
            {"_id": {"$in": lookup_ids}},
        )
    )
    visible_ids = {
        _serialize_id(doc.get("_id"))
        for doc in spot_docs
        if _can_view_spot(repos, viewer_user_id, doc)
    }

    out: list[FavoriteRef] = []
    for row in rows:
        sid = _as_text(row.get("spot_id"))
        if sid not in visible_ids:
            continue
        out.append(
            FavoriteRef(
                spot_id=sid,
                created_at=row.get("created_at") or datetime.now(UTC),
            )
        )
    return out


def get_social_router() -> APIRouter:
    global _SOCIAL_ROUTER
    if _SOCIAL_ROUTER is not None:
        return _SOCIAL_ROUTER

    repos = _repos()
    _SOCIAL_ROUTER = APIRouter(
        prefix="/social",
        tags=["Social"],
        lifespan=_social_lifespan,
    )

    @_SOCIAL_ROUTER.get("/me", response_model=UserPublic)
    def me(current_user: dict[str, Any] = Depends(get_current_user)):
        return _to_user_public(current_user)

    @_SOCIAL_ROUTER.put("/me", response_model=UserPublic)
    def update_me(req: UpdateProfileRequest, current_user: dict[str, Any] = Depends(get_current_user)):
        _ensure_indexes()

        updates: dict[str, Any] = {}

        if req.username is not None:
            username = _normalize_login(req.username)
            if not re.fullmatch(r"[a-z0-9_.-]{3,40}", username):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid username format")
            updates["username"] = username

        if req.email is not None:
            email = _normalize_login(req.email)
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
            if not password_extension.verify_password(current_password, current_hash):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")

            updates["password_hash"] = password_extension.hash_password(req.new_password)

        if not updates:
            return _to_user_public(current_user)

        try:
            repos.users.update_fields({"_id": current_user["_id"]}, updates)
        except DuplicateKeyError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username or email already exists") from e

        updated = repos.users.find_one({"_id": current_user["_id"]})
        if not updated:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Profile update failed")
        return _to_user_public(updated)

    @_SOCIAL_ROUTER.get("/users/search", response_model=list[UserPublic])
    def search_users(
        q: str = Query(default="", max_length=80),
        limit: int = Query(default=20, ge=1, le=50),
        current_user: dict[str, Any] = Depends(get_current_user),
    ):
        query = _as_text(q)
        if not query:
            return []

        me_id = _viewer_user_id(current_user)
        regex = re.compile(re.escape(query), re.IGNORECASE)
        users = list(
            repos.users.collection.find(
                {"$or": [{"username": regex}, {"display_name": regex}]},
                _safe_user_projection(),
            ).limit(limit)
        )

        out: list[UserPublic] = []
        for user_doc in users:
            user_id = _serialize_id(user_doc.get("_id"))
            if user_id == me_id:
                continue
            if _is_blocked_pair(repos, me_id, user_id):
                continue
            out.append(_to_user_public(user_doc))
        return out

    @_SOCIAL_ROUTER.get("/users/{user_id}/profile", response_model=UserPublic)
    def user_profile(user_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
        target_oid = _parse_object_id(user_id)
        target = repos.users.find_one({"_id": target_oid}, _safe_user_projection())
        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        me_id = _viewer_user_id(current_user)
        target_id = _serialize_id(target.get("_id"))
        if me_id != target_id and _is_blocked_pair(repos, me_id, target_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return _to_user_public(target)

    @_SOCIAL_ROUTER.get("/spots", response_model=list[SpotPublic])
    def list_visible_spots(current_user: dict[str, Any] = Depends(get_current_user)):
        me_id = _viewer_user_id(current_user)
        docs = list(repos.spots.collection.find({}).sort("created_at", -1).limit(1500))
        return [_to_spot_public(doc) for doc in docs if _can_view_spot(repos, me_id, doc)]

    @_SOCIAL_ROUTER.post("/spots", response_model=SpotPublic)
    def create_spot(req: SpotUpsertRequest, current_user: dict[str, Any] = Depends(get_current_user)):
        me_id = _viewer_user_id(current_user)
        doc = _build_spot_doc(req, owner_id=me_id)
        inserted_id = repos.spots.insert_one(doc)
        created = repos.spots.find_one({"_id": ObjectId(inserted_id)})
        if not created:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Spot creation failed")
        return _to_spot_public(created)

    @_SOCIAL_ROUTER.put("/spots/{spot_id}", response_model=SpotPublic)
    def update_spot(spot_id: str, req: SpotUpsertRequest, current_user: dict[str, Any] = Depends(get_current_user)):
        existing = _spot_document_by_id(repos, spot_id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spot not found")

        me_id = _viewer_user_id(current_user)
        owner_id = _spot_owner_id(existing)
        if owner_id and owner_id != me_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can edit this spot")

        spot_key = existing.get("_id")
        next_doc = _build_spot_doc(req, owner_id=owner_id or me_id, created_at=existing.get("created_at"))
        repos.spots.update_fields({"_id": spot_key}, next_doc)
        updated = repos.spots.find_one({"_id": spot_key})
        if not updated:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Spot update failed")
        return _to_spot_public(updated)

    @_SOCIAL_ROUTER.delete("/spots/{spot_id}")
    def delete_spot(spot_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
        existing = _spot_document_by_id(repos, spot_id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spot not found")

        me_id = _viewer_user_id(current_user)
        owner_id = _spot_owner_id(existing)
        if owner_id and owner_id != me_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can delete this spot")

        spot_key = existing.get("_id")
        canonical_spot_id = _serialize_id(spot_key)

        repos.spots.collection.delete_one({"_id": spot_key})
        repos.favorites.delete_many({"spot_id": {"$in": [canonical_spot_id, _as_text(spot_id)]}})
        repos.shares.delete_many({"spot_id": {"$in": [canonical_spot_id, _as_text(spot_id)]}})
        return {"ok": True}

    @_SOCIAL_ROUTER.get("/users/{user_id}/spots", response_model=list[SpotPublic])
    def user_spots(user_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
        target_oid = _parse_object_id(user_id)
        target = repos.users.find_one({"_id": target_oid}, _safe_user_projection())
        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        me_id = _viewer_user_id(current_user)
        target_id = _serialize_id(target_oid)
        if me_id != target_id and _is_blocked_pair(repos, me_id, target_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        docs = list(repos.spots.collection.find({"owner_id": target_id}).sort("created_at", -1).limit(1200))
        return [_to_spot_public(doc) for doc in docs if _can_view_spot(repos, me_id, doc)]

    @_SOCIAL_ROUTER.post("/favorites/{spot_id}")
    def add_favorite(spot_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
        spot = _spot_document_by_id(repos, spot_id)
        if not spot:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spot not found")

        me_id = _viewer_user_id(current_user)
        if not _can_view_spot(repos, me_id, spot):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Spot is not visible to you")

        canonical_spot_id = _serialize_id(spot.get("_id"))

        doc = {
            "user_id": me_id,
            "spot_id": canonical_spot_id,
            "created_at": datetime.now(UTC),
        }
        try:
            repos.favorites.insert_one(doc)
        except DuplicateKeyError:
            pass

        return {"ok": True}

    @_SOCIAL_ROUTER.delete("/favorites/{spot_id}")
    def remove_favorite(spot_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
        repos.favorites.collection.delete_one({
            "user_id": _viewer_user_id(current_user),
            "spot_id": spot_id,
        })
        return {"ok": True}

    @_SOCIAL_ROUTER.get("/favorites", response_model=list[FavoriteRef])
    def list_favorites(current_user: dict[str, Any] = Depends(get_current_user)):
        me_id = _viewer_user_id(current_user)
        rows = list(repos.favorites.collection.find({"user_id": me_id}).sort("created_at", -1).limit(2000))
        return _visible_favorite_refs(repos, rows, me_id)

    @_SOCIAL_ROUTER.get("/users/{user_id}/favorites", response_model=list[FavoriteRef])
    def user_favorites(user_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
        target_oid = _parse_object_id(user_id)
        target = repos.users.find_one({"_id": target_oid}, _safe_user_projection())
        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        me_id = _viewer_user_id(current_user)
        if not _can_view_private_user(repos, target, me_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User profile is private")

        target_id = _serialize_id(target_oid)
        rows = list(repos.favorites.collection.find({"user_id": target_id}).sort("created_at", -1).limit(2000))
        return _visible_favorite_refs(repos, rows, me_id)

    @_SOCIAL_ROUTER.get("/follow/requests", response_model=list[FollowRequestRef])
    def follow_requests(current_user: dict[str, Any] = Depends(get_current_user)):
        me_id = _viewer_user_id(current_user)
        rows = list(repos.follow_requests.collection.find({"followee_id": me_id}).sort("created_at", -1).limit(500))
        out: list[FollowRequestRef] = []
        for row in rows:
            follower_id = _as_text(row.get("follower_id"))
            if not ObjectId.is_valid(follower_id):
                continue
            out.append(
                FollowRequestRef(
                    follower_id=follower_id,
                    created_at=row.get("created_at") or datetime.now(UTC),
                )
            )
        return out

    @_SOCIAL_ROUTER.post("/follow/requests/{follower_id}/approve")
    def approve_follow_request(follower_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
        follower_sid = _serialize_id(_parse_object_id(follower_id))
        me_id = _viewer_user_id(current_user)

        request_row = repos.follow_requests.find_one({"follower_id": follower_sid, "followee_id": me_id})
        if not request_row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow request not found")

        try:
            repos.follows.insert_one(
                {
                    "follower_id": follower_sid,
                    "followee_id": me_id,
                    "created_at": datetime.now(UTC),
                }
            )
        except DuplicateKeyError:
            pass

        repos.follow_requests.collection.delete_one({"follower_id": follower_sid, "followee_id": me_id})
        return {"ok": True}

    @_SOCIAL_ROUTER.post("/follow/requests/{follower_id}/reject")
    def reject_follow_request(follower_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
        follower_sid = _serialize_id(_parse_object_id(follower_id))
        me_id = _viewer_user_id(current_user)
        repos.follow_requests.collection.delete_one({"follower_id": follower_sid, "followee_id": me_id})
        return {"ok": True}

    @_SOCIAL_ROUTER.post("/follow/{user_id}")
    def follow_user(user_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
        target_oid = _parse_object_id(user_id)
        target_id = _serialize_id(target_oid)
        me_id = _viewer_user_id(current_user)

        if me_id == target_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot follow yourself")

        target_user = repos.users.find_one({"_id": target_oid}, _safe_user_projection())
        if not target_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if _is_blocked_pair(repos, me_id, target_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot follow this user")

        if _is_following(repos, me_id, target_id):
            return {"ok": True, "status": "following"}

        if bool(target_user.get("follow_requires_approval", False)):
            repos.follow_requests.update_fields(
                {"follower_id": me_id, "followee_id": target_id},
                {"created_at": datetime.now(UTC)},
                upsert=True,
            )
            return {"ok": True, "status": "pending"}

        try:
            repos.follows.insert_one(
                {
                    "follower_id": me_id,
                    "followee_id": target_id,
                    "created_at": datetime.now(UTC),
                }
            )
        except DuplicateKeyError:
            pass

        repos.follow_requests.collection.delete_one({"follower_id": me_id, "followee_id": target_id})
        return {"ok": True, "status": "following"}

    @_SOCIAL_ROUTER.delete("/follow/{user_id}")
    def unfollow_user(user_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
        me_id = _viewer_user_id(current_user)
        target_id = _serialize_id(_parse_object_id(user_id))
        repos.follows.collection.delete_one({"follower_id": me_id, "followee_id": target_id})
        repos.follow_requests.collection.delete_one({"follower_id": me_id, "followee_id": target_id})
        return {"ok": True}

    @_SOCIAL_ROUTER.get("/followers/{user_id}", response_model=list[FollowRef])
    def followers(user_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
        target_oid = _parse_object_id(user_id)
        target_user = repos.users.find_one({"_id": target_oid}, _safe_user_projection())
        if not target_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        me_id = _viewer_user_id(current_user)
        if not _can_view_private_user(repos, target_user, me_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User profile is private")

        target_id = _serialize_id(target_oid)
        rows = list(repos.follows.collection.find({"followee_id": target_id}).sort("created_at", -1).limit(1200))
        out: list[FollowRef] = []
        for row in rows:
            follower_id = _as_text(row.get("follower_id"))
            if not ObjectId.is_valid(follower_id):
                continue
            if _is_blocked_pair(repos, me_id, follower_id):
                continue
            out.append(
                FollowRef(
                    user_id=follower_id,
                    created_at=row.get("created_at") or datetime.now(UTC),
                )
            )
        return out

    @_SOCIAL_ROUTER.get("/following/{user_id}", response_model=list[FollowRef])
    def following(user_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
        target_oid = _parse_object_id(user_id)
        target_user = repos.users.find_one({"_id": target_oid}, _safe_user_projection())
        if not target_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        me_id = _viewer_user_id(current_user)
        if not _can_view_private_user(repos, target_user, me_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User profile is private")

        target_id = _serialize_id(target_oid)
        rows = list(repos.follows.collection.find({"follower_id": target_id}).sort("created_at", -1).limit(1200))
        out: list[FollowRef] = []
        for row in rows:
            followee_id = _as_text(row.get("followee_id"))
            if not ObjectId.is_valid(followee_id):
                continue
            if _is_blocked_pair(repos, me_id, followee_id):
                continue
            out.append(
                FollowRef(
                    user_id=followee_id,
                    created_at=row.get("created_at") or datetime.now(UTC),
                )
            )
        return out

    @_SOCIAL_ROUTER.delete("/followers/{user_id}")
    def remove_follower(user_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
        me_id = _viewer_user_id(current_user)
        follower_id = _serialize_id(_parse_object_id(user_id))
        repos.follows.collection.delete_one({"follower_id": follower_id, "followee_id": me_id})
        repos.follow_requests.collection.delete_one({"follower_id": follower_id, "followee_id": me_id})
        return {"ok": True}

    @_SOCIAL_ROUTER.post("/block/{user_id}")
    def block_user(user_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
        me_id = _viewer_user_id(current_user)
        target_id = _serialize_id(_parse_object_id(user_id))
        if me_id == target_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot block yourself")

        repos.blocks.update_fields(
            {"blocker_id": me_id, "blocked_id": target_id},
            {"created_at": datetime.now(UTC)},
            upsert=True,
        )

        repos.follows.collection.delete_many(
            {
                "$or": [
                    {"follower_id": me_id, "followee_id": target_id},
                    {"follower_id": target_id, "followee_id": me_id},
                ]
            }
        )
        repos.follow_requests.collection.delete_many(
            {
                "$or": [
                    {"follower_id": me_id, "followee_id": target_id},
                    {"follower_id": target_id, "followee_id": me_id},
                ]
            }
        )
        return {"ok": True}

    @_SOCIAL_ROUTER.delete("/block/{user_id}")
    def unblock_user(user_id: str, current_user: dict[str, Any] = Depends(get_current_user)):
        me_id = _viewer_user_id(current_user)
        target_id = _serialize_id(_parse_object_id(user_id))
        repos.blocks.collection.delete_one({"blocker_id": me_id, "blocked_id": target_id})
        return {"ok": True}

    @_SOCIAL_ROUTER.get("/blocked", response_model=list[BlockRef])
    def blocked_users(current_user: dict[str, Any] = Depends(get_current_user)):
        me_id = _viewer_user_id(current_user)
        rows = list(repos.blocks.collection.find({"blocker_id": me_id}).sort("created_at", -1).limit(500))
        out: list[BlockRef] = []
        for row in rows:
            blocked_id = _as_text(row.get("blocked_id"))
            if not ObjectId.is_valid(blocked_id):
                continue
            out.append(
                BlockRef(
                    user_id=blocked_id,
                    created_at=row.get("created_at") or datetime.now(UTC),
                )
            )
        return out

    @_SOCIAL_ROUTER.post("/share/{spot_id}")
    def share_spot(spot_id: str, req: ShareRequest, current_user: dict[str, Any] = Depends(get_current_user)):
        spot = _spot_document_by_id(repos, spot_id)
        if not spot:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spot not found")

        me_id = _viewer_user_id(current_user)
        if not _can_view_spot(repos, me_id, spot):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Spot is not visible to you")

        canonical_spot_id = _serialize_id(spot.get("_id"))

        repos.shares.insert_one(
            {
                "user_id": me_id,
                "spot_id": canonical_spot_id,
                "message": req.message,
                "created_at": datetime.now(UTC),
            }
        )
        return {"ok": True}

    @_SOCIAL_ROUTER.post(
        "/support/tickets",
        response_model=SupportTicketPublic,
        status_code=status.HTTP_201_CREATED,
    )
    def create_support_ticket(req: SupportTicketRequest, current_user: dict[str, Any] = Depends(get_current_user)):
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

        inserted_id = repos.support_tickets.insert_one(doc)
        row = repos.support_tickets.find_one({"_id": ObjectId(inserted_id)})
        if not row:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Support ticket creation failed",
            )
        return _to_support_ticket_public(row)

    return _SOCIAL_ROUTER
