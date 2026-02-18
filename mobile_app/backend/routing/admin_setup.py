from __future__ import annotations

import os
from datetime import UTC, datetime

from bson import ObjectId
from pymongo import ASCENDING

from data.mongo_repository import MongoRepository
from data.dto import AuthUserRecord
from routing.auth_routes import password_extension


ADMIN_DEFAULT_USERNAME = os.getenv("ADMIN_USERNAME", "admin").strip().lower()
ADMIN_DEFAULT_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@123!")
ADMIN_DEFAULT_EMAIL = os.getenv("ADMIN_EMAIL", "admin@spotonsight.app").strip().lower()
ADMIN_DEFAULT_DISPLAY = os.getenv("ADMIN_DISPLAY", "System Administrator").strip()


def ensure_admin_user(repository: MongoRepository) -> dict | None:
    """Create admin user if it doesn't exist. Returns the admin user document or None."""
    
    existing = repository.find_one({"username": ADMIN_DEFAULT_USERNAME})
    if existing:
        if not existing.get("is_admin", False):
            repository.update_one(
                {"_id": existing["_id"]},
                {"$set": {"is_admin": True}}
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
    return bool(user_doc.get("is_admin", False))


def get_admin_repository() -> MongoRepository:
    """Get the auth repository for admin operations."""
    return MongoRepository(
        collection_name="users",
        model_type=AuthUserRecord,
        db_name="SpotOnSightAuth",
    )
