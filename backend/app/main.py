from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import connect_to_mongo, close_mongo_connection
from app.routers import auth

app = FastAPI()

# CORS configuration to allow your React frontend and Render backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://creatorpilot-backend-70xt.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database event handlers
app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)

# Include routers
app.include_router(auth.router, prefix="/api", tags=["Auth"])

@app.get("/")
def root():
    return {"message": "CreatorPilot AI Backend is running!"}