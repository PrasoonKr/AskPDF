from functools import lru_cache
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os
from dotenv import load_dotenv

from backend.bootstrap import startup

load_dotenv("backend/.env")

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

application_cache = {}

def get_application(current_user=Depends(get_current_user)):
    user_email = current_user.get("email") or current_user.get("sub", "default")
    if user_email not in application_cache:
        application_cache[user_email] = startup(user_email)
    return application_cache[user_email]