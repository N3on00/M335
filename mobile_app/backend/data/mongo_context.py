from __future__ import annotations

import os

from pymongo import MongoClient


def mongo_client() -> MongoClient:
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    return MongoClient(mongo_url)


def social_db_name() -> str:
    return os.getenv("MONGO_AUTH_DB", "witterungsstation")


def spots_db_name() -> str:
    return os.getenv("MONGO_SPOTS_DB", "spot_on_sight")


def social_db():
    return mongo_client()[social_db_name()]


def spots_db():
    return mongo_client()[spots_db_name()]
