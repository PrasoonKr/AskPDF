from functools import lru_cache
from collections import OrderedDict
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os
from dotenv import load_dotenv

from backend.bootstrap import startup

load_dotenv("backend/.env", override=True)

security = HTTPBearer()
JWT_SECRET = os.getenv("JWT_SECRET", "super_secret_jwt_key_for_ai_research_assistant")

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# LRU application cache — evicts oldest user when capacity is exceeded
# On t3.small (2GB RAM), each Application holds a FAISS index + BM25 index
MAX_CACHED_USERS = 5

class _ApplicationLRU:
    """Simple LRU cache for Application instances to prevent OOM on small EC2 instances."""
    def __init__(self, max_size: int = MAX_CACHED_USERS):
        self._cache = OrderedDict()
        self._max_size = max_size

    def get_or_create(self, user_email: str):
        if user_email in self._cache:
            self._cache.move_to_end(user_email)
            return self._cache[user_email]
        if len(self._cache) >= self._max_size:
            evicted_email, _ = self._cache.popitem(last=False)
            print(f"[AppCache] Evicted user '{evicted_email}' to free memory.", flush=True)
        app = startup(user_email)
        self._cache[user_email] = app
        return app

_app_cache = _ApplicationLRU()

def get_application(current_user=Depends(get_current_user)):
    user_email = current_user.get("email") or current_user.get("sub", "default")
    return _app_cache.get_or_create(user_email)