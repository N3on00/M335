from functools import wraps
import json
from datetime import UTC, datetime
from typing import Any, Callable, Dict, Type, TypeVar

from bson import ObjectId, json_util
from fastapi import APIRouter, Body, Depends, HTTPException, Response, status
from pydantic import BaseModel, ValidationError
from pymongo.errors import DuplicateKeyError

# Generic type for Pydantic models
T = TypeVar('T', bound=BaseModel)


class GenericCrudRouter:
    """Generic CRUD router builder with model validation and ObjectId handling."""

    def __init__(
        self,
        model: Type[T],
        repository,
        prefix: str,
        tags: list[str] | None = None,
    ) -> None:
        self.model = model
        self.repository = repository
        self.prefix = prefix
        self.tags = tags or [prefix.strip('/')]

    def route_dependencies(self) -> list[Any]:
        return []

    def _validate_object_id(self, entity_id: str) -> ObjectId:
        if not ObjectId.is_valid(entity_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ID format",
            )
        return ObjectId(entity_id)

    def handle_exceptions(self, func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=getattr(e, 'status_code', 500),
                    detail={
                        "error": str(e),
                        "type": e.__class__.__name__,
                    },
                )

        return wrapper

    def with_object_id_validation(self, func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(entity_id: str, *args, **kwargs):
            validated = self._validate_object_id(entity_id)
            return await func(validated, *args, **kwargs)

        return wrapper

    def build(self) -> APIRouter:
        model = self.model
        repository = self.repository

        router = APIRouter(
            prefix=self.prefix,
            tags=self.tags,
            dependencies=self.route_dependencies(),
        )

        @router.post("/")
        @self.handle_exceptions
        async def create(entity_data: Dict[str, Any] = Body(...)):
            try:
                entity = model.model_validate(entity_data)
            except ValidationError as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=e.errors(),
                ) from e
            entity_id = repository.create(entity)
            return {"id": str(entity_id)}

        @router.get("/")
        @self.handle_exceptions
        async def read_all():
            entities = repository.read_all()
            return json.loads(json_util.dumps(entities))

        @router.get("/{entity_id}")
        @self.handle_exceptions
        @self.with_object_id_validation
        async def read(entity_id: str):
            entity = repository.read(entity_id)
            if not entity:
                raise HTTPException(status.HTTP_404_NOT_FOUND)
            return json.loads(json_util.dumps(entity))

        @router.put("/{entity_id}")
        @self.handle_exceptions
        @self.with_object_id_validation
        async def update(entity_id: str, entity_data: Dict[str, Any] = Body(...)):
            try:
                entity = model.model_validate(entity_data)
            except ValidationError as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=e.errors(),
                ) from e
            result = repository.update(entity_id, entity)
            if not result.modified_count:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Entity not found")
            return {"modified_count": result.modified_count}

        @router.delete("/{entity_id}")
        @self.handle_exceptions
        @self.with_object_id_validation
        async def delete(entity_id: str):
            result = repository.delete(entity_id)
            if result.deleted_count == 0:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Entity not found")
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        return router


class AuthenticatedCrudRouter(GenericCrudRouter):
    """Generic CRUD router that adds auth dependency to all operations."""

    def __init__(
        self,
        model: Type[T],
        repository,
        prefix: str,
        tags: list[str] | None = None,
        auth_dependency: Callable[..., Any] | None = None,
    ) -> None:
        super().__init__(model=model, repository=repository, prefix=prefix, tags=tags)
        if auth_dependency is None:
            raise ValueError("AuthenticatedCrudRouter requires an auth dependency")
        self.auth_dependency = auth_dependency

    def route_dependencies(self) -> list[Any]:
        return [Depends(self.auth_dependency)]


class AuthSessionRouter(GenericCrudRouter):
    """Auth router extension built on top of GenericCrudRouter."""

    def __init__(
        self,
        repository,
        register_model: Type[BaseModel],
        login_model: Type[BaseModel],
        user_public_model: Type[BaseModel],
        token_response_model: Type[BaseModel],
        token_extension,
        password_extension,
        prefix: str = "/auth",
        tags: list[str] | None = None,
    ) -> None:
        super().__init__(model=register_model, repository=repository, prefix=prefix, tags=tags or ["Auth"])
        self.register_model = register_model
        self.login_model = login_model
        self.user_public_model = user_public_model
        self.token_response_model = token_response_model
        self.token_extension = token_extension
        self.password_extension = password_extension

    @staticmethod
    def _as_text(value: Any) -> str:
        return str(value or "").strip()

    def _normalize_login(self, value: Any) -> str:
        return self._as_text(value).lower()

    def _normalize_social_accounts(self, value: Any) -> dict[str, str]:
        if not isinstance(value, dict):
            return {}
        out: dict[str, str] = {}
        for key, item in value.items():
            k = self._as_text(key)
            v = self._as_text(item)
            if not k or not v:
                continue
            if len(k) > 40 or len(v) > 500:
                continue
            out[k] = v
        return out

    def _to_user_public(self, user_doc: dict[str, Any]) -> BaseModel:
        payload = {
            "id": self._as_text(user_doc.get("_id")),
            "username": self._as_text(user_doc.get("username")),
            "email": self._as_text(user_doc.get("email")),
            "display_name": self._as_text(user_doc.get("display_name") or user_doc.get("username")),
            "bio": self._as_text(user_doc.get("bio")),
            "avatar_image": self._as_text(user_doc.get("avatar_image")),
            "social_accounts": self._normalize_social_accounts(user_doc.get("social_accounts")),
            "follow_requires_approval": bool(user_doc.get("follow_requires_approval", False)),
            "created_at": user_doc.get("created_at") or datetime.now(UTC),
        }
        return self.user_public_model.model_validate(payload)

    def _to_auth_response(self, user_doc: dict[str, Any]) -> BaseModel:
        user_id = self._as_text(user_doc.get("_id"))
        username = self._as_text(user_doc.get("username"))
        access_token = self.token_extension.issue_access_token(user_id=user_id, username=username)
        payload = {
            "access_token": access_token,
            "token_type": "bearer",
            "user": self._to_user_public(user_doc),
        }
        return self.token_response_model.model_validate(payload)

    def _build_auth_user_document(self, req: BaseModel, password_hash: str) -> dict[str, Any]:
        username = self._normalize_login(getattr(req, "username", ""))
        email = self._normalize_login(getattr(req, "email", ""))
        display_name = self._as_text(getattr(req, "display_name", "")) or username

        return {
            "username": username,
            "email": email,
            "password_hash": self._as_text(password_hash),
            "display_name": display_name,
            "bio": "",
            "avatar_image": "",
            "social_accounts": {},
            "follow_requires_approval": False,
            "created_at": datetime.now(UTC),
        }

    def _find_user_by_login(self, repository, username_or_email: str) -> dict[str, Any] | None:
        login = self._normalize_login(username_or_email)
        if not login:
            return None
        return repository.find_one({"$or": [{"username": login}, {"email": login}]})

    def _create_registered_user(self, repository, req: BaseModel, password_hash: str) -> dict[str, Any]:
        user_doc = self._build_auth_user_document(req, password_hash=password_hash)
        inserted_id = repository.insert_one(user_doc)
        return repository.find_one({"_id": ObjectId(str(inserted_id))})

    def build(self) -> APIRouter:
        repository = self.repository

        router = APIRouter(prefix=self.prefix, tags=self.tags)

        @router.post("/register", response_model=self.token_response_model)
        @self.handle_exceptions
        async def register(payload: Dict[str, Any] = Body(...)):
            try:
                req = self.register_model.model_validate(payload)
            except ValidationError as e:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors()) from e

            password_hash = self.password_extension.hash_password(req.password)

            try:
                user_doc = self._create_registered_user(repository, req, password_hash=password_hash)
            except DuplicateKeyError as e:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Username or email already exists",
                ) from e

            if not user_doc:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="User creation failed",
                )

            return self._to_auth_response(user_doc)

        @router.post("/login", response_model=self.token_response_model)
        @self.handle_exceptions
        async def login(payload: Dict[str, Any] = Body(...)):
            try:
                req = self.login_model.model_validate(payload)
            except ValidationError as e:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors()) from e

            user_doc = self._find_user_by_login(repository, req.username_or_email)
            if not user_doc:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username/email or password",
                )

            password_hash = self._as_text(user_doc.get("password_hash"))
            if not self.password_extension.verify_password(req.password, password_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username/email or password",
                )

            return self._to_auth_response(user_doc)

        return router


def router_create(
    model: Type[T],
    repository,
    prefix: str,
    tags: list[str] | None = None,
) -> APIRouter:
    return GenericCrudRouter(
        model=model,
        repository=repository,
        prefix=prefix,
        tags=tags,
    ).build()


def router_create_authenticated(
    model: Type[T],
    repository,
    prefix: str,
    auth_dependency: Callable[..., Any],
    tags: list[str] | None = None,
) -> APIRouter:
    return AuthenticatedCrudRouter(
        model=model,
        repository=repository,
        prefix=prefix,
        tags=tags,
        auth_dependency=auth_dependency,
    ).build()


def router_create_auth_sessions(
    repository,
    register_model: Type[BaseModel],
    login_model: Type[BaseModel],
    user_public_model: Type[BaseModel],
    token_response_model: Type[BaseModel],
    token_extension,
    password_extension,
    prefix: str = "/auth",
    tags: list[str] | None = None,
) -> APIRouter:
    return AuthSessionRouter(
        repository=repository,
        register_model=register_model,
        login_model=login_model,
        user_public_model=user_public_model,
        token_response_model=token_response_model,
        token_extension=token_extension,
        password_extension=password_extension,
        prefix=prefix,
        tags=tags,
    ).build()
