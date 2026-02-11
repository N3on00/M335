from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Type, TypeVar

from fastapi import APIRouter
from pydantic import BaseModel

from data.mongo_repository import MongoRepository
from routing.router import router_create

T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True)
class EntityBinding:
    model: Type[T]
    collection: str
    prefix: str
    tags: list[str]
    router: APIRouter


_REGISTRY: list[EntityBinding] = []


def get_routers() -> list[APIRouter]:
    return [b.router for b in _REGISTRY]


def mongo_entity(
    *,
    collection: str,
    prefix: str | None = None,
    tags: list[str] | None = None,
) -> Callable[[Type[T]], Type[T]]:
    """Class decorator that registers a model and auto-creates its CRUD router."""

    def decorator(model_cls: Type[T]) -> Type[T]:
        effective_prefix = prefix or f"/{collection}"
        effective_tags = tags or [collection]

        repo = MongoRepository(collection_name=collection, model_type=model_cls)
        router = router_create(
            model=model_cls,
            repository=repo,
            prefix=effective_prefix,
            tags=effective_tags,
        )

        _REGISTRY.append(
            EntityBinding(
                model=model_cls,
                collection=collection,
                prefix=effective_prefix,
                tags=effective_tags,
                router=router,
            )
        )
        return model_cls

    return decorator
