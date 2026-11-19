from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up CreatorPilot AI backend...")
    yield
    print("Shutting down CreatorPilot AI backend...")

app = FastAPI(
    title="CreatorPilot AI API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Authentication Router without the extra /api prefix so it matches /auth/login directly
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])

@app.get("/")
async def read_root():
    return {"status": "healthy", "message": "CreatorPilot AI Backend is running!"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}