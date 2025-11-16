import os
from typing import Any, Dict, List, Optional
from datetime import datetime
from pymongo import MongoClient
from pymongo.collection import Collection

# Environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "app_db")

client: Optional[MongoClient] = None
_db = None

try:
    client = MongoClient(DATABASE_URL)
    _db = client[DATABASE_NAME]
except Exception:
    client = None
    _db = None

# Public export for other modules
db = _db


def get_collection(name: str) -> Optional[Collection]:
    if db is None:
        return None
    return db[name]


def timestamp_now() -> datetime:
    return datetime.utcnow()


def create_document(collection_name: str, data: Dict[str, Any]) -> Optional[str]:
    col = get_collection(collection_name)
    if col is None:
        return None
    now = timestamp_now()
    data["created_at"] = now
    data["updated_at"] = now
    result = col.insert_one(data)
    return str(result.inserted_id)


def get_documents(collection_name: str, filter_dict: Dict[str, Any] = None, limit: int = 0) -> List[Dict[str, Any]]:
    col = get_collection(collection_name)
    if col is None:
        return []
    cursor = col.find(filter_dict or {})
    if limit and limit > 0:
        cursor = cursor.limit(limit)
    items = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        items.append(doc)
    return items


def update_document(collection_name: str, filter_dict: Dict[str, Any], update_fields: Dict[str, Any]) -> int:
    col = get_collection(collection_name)
    if col is None:
        return 0
    update_fields["updated_at"] = timestamp_now()
    result = col.update_one(filter_dict, {"$set": update_fields})
    return result.modified_count


def delete_document(collection_name: str, filter_dict: Dict[str, Any]) -> int:
    col = get_collection(collection_name)
    if col is None:
        return 0
    result = col.delete_one(filter_dict)
    return result.deleted_count
