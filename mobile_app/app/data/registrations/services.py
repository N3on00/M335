from __future__ import annotations

from core.di import service_provider
from data.repositories.spots_repository import SpotsRepository
from data.services.api_client import ApiClient
from data.services.auth_service import AuthService
from data.services.spots_service import SpotsService


@service_provider(service_id="api_client")
def api_client(ctx):
    cfg = ctx.state.config
    return ApiClient(base_url=cfg.api_base_url, timeout_s=cfg.request_timeout_s)


@service_provider(service_id="spots_repo")
def spots_repo(ctx):
    api = ctx.service("api_client")
    return SpotsRepository(api, auth_token_provider=lambda: ctx.state.auth_token)


@service_provider(service_id="spots_service")
def spots_service(ctx):
    repo = ctx.service("spots_repo")
    return SpotsService(repo)


@service_provider(service_id="auth_service")
def auth_service(ctx):
    api = ctx.service("api_client")
    return AuthService(api, ctx.state)
