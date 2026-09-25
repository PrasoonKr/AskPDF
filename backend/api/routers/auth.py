from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests
import jwt
import datetime

import os
from dotenv import load_dotenv

load_dotenv("backend/.env")

router = APIRouter(prefix="/auth", tags=["auth"])

class GoogleLoginRequest(BaseModel):
    credential: str

class LoginResponse(BaseModel):
    token: str
    user: dict

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "YOUR_CLIENT_ID_HERE")
JWT_SECRET = os.getenv("JWT_SECRET", "super_secret_jwt_key_for_ai_research_assistant")

@router.post("/google", response_model=LoginResponse)
async def google_login(req: GoogleLoginRequest):
    try:
        if CLIENT_ID == "YOUR_CLIENT_ID_HERE":
            # For testing without a real client ID, we could mock the response, but it's better to fail 
            # and wait for the real client ID. 
            pass
            
        idinfo = id_token.verify_oauth2_token(req.credential, requests.Request(), CLIENT_ID)
        
        email = idinfo['email']
        name = idinfo.get('name', '')
        picture = idinfo.get('picture', '')
        
        # Generate our own JWT
        expiration = datetime.datetime.utcnow() + datetime.timedelta(days=7)
        token = jwt.encode({
            "sub": email,
            "email": email,
            "name": name,
            "picture": picture,
            "exp": expiration.timestamp()
        }, JWT_SECRET, algorithm="HS256")
        
        return LoginResponse(
            token=token,
            user={"email": email, "name": name, "picture": picture}
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


@router.post("/dev-login", response_model=LoginResponse)
async def dev_login():
    email = "dev@example.com"
    name = "Developer"
    expiration = datetime.datetime.utcnow() + datetime.timedelta(days=7)
    token = jwt.encode({
        "sub": email,
        "email": email,
        "name": name,
        "picture": "",
        "exp": expiration.timestamp()
    }, JWT_SECRET, algorithm="HS256")
    
    return LoginResponse(
        token=token,
        user={"email": email, "name": name, "picture": ""}
    )

