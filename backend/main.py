""""backend/main.py

FastAPI application entry point. Registers all routers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from database import connect_to_mongo, close_mongo_connection
from routers import auth, calendar, thumbnails, audience, brand, dashboard

app = FastAPI(title="CreatorPilot AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

# Include authentication router
app.include_router(auth.router)

# Include calendar & kanban router
app.include_router(calendar.router)

# Include thumbnail lab router
app.include_router(thumbnails.router)

# Include audience intelligence router
app.include_router(audience.router)

# Include brand assistant router
app.include_router(brand.router)
app.include_router(dashboard.router)

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "CreatorPilot AI"}