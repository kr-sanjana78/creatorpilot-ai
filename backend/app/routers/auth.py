from fastapi import APIRouter, HTTPException, status
from passlib.context import CryptContext
from app.database import get_database
from app.schemas.auth import UserCreate, UserLogin, Token

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/register")
async def register(user: UserCreate):
    db = get_database()
    users_collection = db["users"]
    
    # Check if user already exists
    existing_user = users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password before saving
    hashed_password = pwd_context.hash(user.password)
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    
    users_collection.insert_one(user_dict)
    
    return {"message": "User registered successfully", "email": user.email}

@router.post("/login", response_model=Token)
async def login(user: UserLogin):
    db = get_database()
    users_collection = db["users"]
    
    # Find user by email and verify password using passlib
    db_user = users_collection.find_one({"email": user.email})
    if not db_user or not pwd_context.verify(user.password, db_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Return access token
    return {"access_token": f"fake-jwt-token-for-{user.email}", "token_type": "bearer"}