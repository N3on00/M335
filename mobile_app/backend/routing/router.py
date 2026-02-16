from functools import wraps
import json
import traceback
from typing import Any, Callable, Dict, Type, TypeVar

from bson import ObjectId, json_util
from fastapi import APIRouter, Body, Depends, HTTPException, Response, status
from pydantic import BaseModel, ValidationError

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
                        "traceback": traceback.format_exc().splitlines(),
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
        async def read(entity_id: ObjectId):
            entity = repository.read(entity_id)
            if not entity:
                raise HTTPException(status.HTTP_404_NOT_FOUND)
            return json.loads(json_util.dumps(entity))

        @router.put("/{entity_id}")
        @self.handle_exceptions
        @self.with_object_id_validation
        async def update(entity_id: ObjectId, entity_data: Dict[str, Any] = Body(...)):
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
        async def delete(entity_id: ObjectId):
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
