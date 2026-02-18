from __future__ import annotations

import os
from datetime import UTC, datetime
from functools import wraps
from typing import Callable

from bson import ObjectId

from fastapi import Depends, HTTPException, status

from data.dto import AuthUserRecord
from routing.auth_routes import password_extension, get_auth_user_repository


ADMIN_DEFAULT_USERNAME = os.getenv("ADMIN_USERNAME", "admin").strip().lower()
ADMIN_DEFAULT_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@123!")
ADMIN_DEFAULT_EMAIL = os.getenv("ADMIN_EMAIL", "admin@spotonsight.app").strip().lower()
ADMIN_DEFAULT_DISPLAY = os.getenv("ADMIN_DISPLAY", "System Administrator").strip()


def _is_admin_user(user_doc: dict) -> bool:
    """Check if a user document represents an admin."""
    return bool(user_doc.get("is_admin", False))


def get_current_admin_user(current_user: dict = Depends(lambda: None)) -> dict:
    """Dependency that requires admin privileges.
    
    Usage:
        @router.get("/admin-only")
        def admin_endpoint(admin: dict = Depends(get_current_admin_user)):
            ...
    """
    if current_user is None:
        from routing.auth_routes import get_current_user
        current_user = get_current_user()
    
    if not _is_admin_user(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def require_admin(func: Callable) -> Callable:
    """Decorator for requiring admin privileges on endpoint functions.
    
    Usage:
        @require_admin
        def admin_only_function(current_user: dict = Depends(get_current_user)):
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        current_user = kwargs.get('current_user')
        if current_user is None:
            from routing.auth_routes import get_current_user
            current_user = get_current_user()
        
        if not _is_admin_user(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )
        return await func(*args, **kwargs)
    return wrapper


def ensure_admin_user() -> dict | None:
    """Create admin user if it doesn't exist. Returns the admin user document or None."""
    
    repository = get_auth_user_repository()
    existing = repository.find_one({"username": ADMIN_DEFAULT_USERNAME})
    
    if existing:
        if not _is_admin_user(existing):
            repository.update_fields(
                {"_id": existing["_id"]},
                {"is_admin": True}
            )
            existing["is_admin"] = True
        return existing

    admin_user = AuthUserRecord(
        username=ADMIN_DEFAULT_USERNAME,
        email=ADMIN_DEFAULT_EMAIL,
        password_hash=password_extension.hash_password(ADMIN_DEFAULT_PASSWORD),
        display_name=ADMIN_DEFAULT_DISPLAY,
        bio="System Administrator - Full access to all features",
        is_admin=True,
        created_at=datetime.now(UTC),
    )

    doc = admin_user.model_dump()
    doc["_id"] = ObjectId()
    
    try:
        repository.insert_one(doc)
        created = repository.find_one({"username": ADMIN_DEFAULT_USERNAME})
        print(f"[STARTUP] Admin user '{ADMIN_DEFAULT_USERNAME}' created successfully.")
        return created
    except Exception as e:
        print(f"[STARTUP] Failed to create admin user: {e}")
        return None


def is_admin_user(user_doc: dict) -> bool:
    """Check if a user document represents an admin."""
    return _is_admin_user(user_doc)
