from __future__ import annotations

from datetime import UTC, datetime, timedelta
import os
from typing import Any

from bson import ObjectId
from fastapi import APIRouter
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pymongo import ASCENDING

from data.mongo_repository import MongoRepository
from routing.router import router_create_auth_sessions


_PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")
_OAUTH2_SCHEME = OAuth2PasswordBearer(tokenUrl="/auth/login")


class TokenExtension:
    def __init__(self) -> None:
        self.secret_key = str(os.getenv("JWT_SECRET") or "change-this-secret").strip() or "change-this-secret"
        self.algorithm = str(os.getenv("JWT_ALGORITHM") or "HS256").strip() or "HS256"
        self.expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES") or "60")

    def issue_access_token(self, *, user_id: str, username: str) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "username": str(username or ""),
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=self.expire_minutes)).timestamp()),
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_access_token(self, token: str) -> dict[str, Any]:
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])


class PasswordExtension:
    @staticmethod
    def hash_password(password: str) -> str:
        return _PWD_CONTEXT.hash(str(password or ""))

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return _PWD_CONTEXT.verify(str(plain_password or ""), str(hashed_password or ""))


token_extension = TokenExtension()
password_extension = PasswordExtension()
_auth_router: APIRouter | None = None
_auth_repository: MongoRepository | None = None


def _auth_db_name() -> str:
    return str(os.getenv("MONGO_AUTH_DB") or "SpotOnSightAuth").strip() or "SpotOnSightAuth"


def _auth_repository_instance() -> MongoRepository:
    global _auth_repository
    if _auth_repository is not None:
        return _auth_repository

    from data.dto import AuthUserRecord

    repo = MongoRepository(
        collection_name="users",
        model_type=AuthUserRecord,
        db_name=_auth_db_name(),
    )
    repo.collection.create_index([("username", ASCENDING)], unique=True)
    repo.collection.create_index([("email", ASCENDING)], unique=True)
    repo.collection.create_index([("display_name", ASCENDING)])

    _auth_repository = repo
    return _auth_repository


def get_auth_user_repository() -> MongoRepository:
    return _auth_repository_instance()


def _find_user_by_id(user_id: str) -> dict[str, Any] | None:
    text = str(user_id or "").strip()
    if not ObjectId.is_valid(text):
        return None
    return _auth_repository_instance().find_one({"_id": ObjectId(text)})


def get_current_user(token: str = Depends(_OAUTH2_SCHEME)) -> dict[str, Any]:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = token_extension.decode_access_token(token)
    except JWTError as e:
        raise credentials_error from e

    user_id = str(payload.get("sub") or "").strip()
    if not user_id:
        raise credentials_error

    user_doc = _find_user_by_id(user_id)
    if not user_doc:
        raise credentials_error

    return user_doc


def get_auth_router() -> APIRouter:
    global _auth_router
    if _auth_router is not None:
        return _auth_router

    from data.dto import AuthTokenResponse, LoginRequest, RegisterRequest, UserPublic

    _auth_router = router_create_auth_sessions(
        repository=_auth_repository_instance(),
        register_model=RegisterRequest,
        login_model=LoginRequest,
        user_public_model=UserPublic,
        token_response_model=AuthTokenResponse,
        token_extension=token_extension,
        password_extension=password_extension,
        prefix="/auth",
        tags=["Auth"],
    )
    return _auth_router
