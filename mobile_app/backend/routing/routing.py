from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routing.auth_routes import get_auth_router, get_social_router
from routing.registry import get_routers


class Routing:
    """FastAPI app builder.

    Important: DTO modules must be imported before building the app,
    so @mongo_entity decorators can register their routers.
    """

    def __init__(self) -> None:
        self._app = FastAPI()
        self._app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

        for router in get_routers():
            self._app.include_router(router)

        self._app.include_router(get_auth_router())
        self._app.include_router(get_social_router())

    def get_app(self) -> FastAPI:
        return self._app
