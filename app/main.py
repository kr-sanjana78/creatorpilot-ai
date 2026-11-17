from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection
from app.routers import auth
from app.routers.ai import router as ai_router  # Import your AI router

app = FastAPI(title="CreatorPilot AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register your routers
app.include_router(auth.router)
app.include_router(ai_router)  # Register the AI router here

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "CreatorPilot AI"}