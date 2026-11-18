from fastapi import APIRouter, HTTPException, status
from pwdlib import PasswordHash
import jwt
from datetime import datetime, timedelta, timezone

from backend.database import get_database
from backend.config import settings
from backend.schemas.auth import UserCreate, UserLogin, Token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
password_hash = PasswordHash.recommended()

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    db = get_database()
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = password_hash.hash(user.password)
    new_user = {
        "email": user.email,
        "password": hashed_password,
        "full_name": user.full_name,
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.users.insert_one(new_user)
    return {"message": "User registered successfully"}

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    db = get_database()
    user = await db.users.find_one({"email": credentials.email})
    
    if not user or not password_hash.verify(credentials.password, user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user["email"], "exp": expire}
    access_token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    
    return {"access_token": access_token, "token_type": "bearer"}
    