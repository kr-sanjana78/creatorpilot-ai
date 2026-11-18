from fastapi import APIRouter, HTTPException, status, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from google import genai
from app.config import settings
import jwt

router = APIRouter(prefix="/ai", tags=["AI Generation"])

client = genai.Client(api_key=settings.GEMINI_API_KEY)

SECRET_KEY = "your-super-secret-key-change-in-production"
ALGORITHM = "HS256"

security = HTTPBearer()

class ScriptRequest(BaseModel):
    prompt: str
    platform: str = "YouTube"

class ScriptResponse(BaseModel):
    script: str

class StrategyRequest(BaseModel):
    topic: str
    platform: str = "YouTube"

class StrategyResponse(BaseModel):
    title: str
    hook: str
    outline: list[str]
    call_to_action: str

# Dependency to verify the JWT token
async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return email
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

@router.post("/generate-script", response_model=ScriptResponse)
async def generate_script(request: ScriptRequest, current_user: str = Depends(verify_token)):
    try:
        full_prompt = (
            f"Write an engaging video script for a {request.platform} video "
            f"based on the following idea/topic: {request.prompt}. "
            "Keep it structured with an intro, body, and call to action."
        )
        
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=full_prompt,
        )
        
        return ScriptResponse(script=response.text)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate script: {str(e)}"
        )

@router.post("/strategy", response_model=StrategyResponse)
async def generate_strategy(request: StrategyRequest, current_user: str = Depends(verify_token)):
    try:
        full_prompt = (
            f"Generate a content strategy for a {request.platform} video about '{request.topic}'. "
            "Provide a catchy title, an engaging opening hook, a bulleted outline of main points, "
            "and a strong call to action (CTA)."
        )
        
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=full_prompt,
        )
        
        return StrategyResponse(
            title=f"Mastering {request.topic}",
            hook="Want to know the secret that nobody tells you?",
            outline=["Introduction", "Core Concept", "Common Mistakes", "Summary"],
            call_to_action="Subscribe for more tips!"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate strategy: {str(e)}"
        )