from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import connect_to_mongo, close_mongo_connection
from app.routers import auth

app = FastAPI(title="CreatorPilot AI Backend")

# CORS configuration allowing local development and production frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "https://creatorpilot-backend-70xt.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database startup and shutdown events
app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)

# Include API routers
app.include_router(auth.router, prefix="/api", tags=["Auth"])

@app.get("/")
def read_root():
    return {"status": "online", "message": "CreatorPilot AI Backend is running"}