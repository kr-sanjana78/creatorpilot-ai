from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import connect_to_mongo, close_mongo_connection
from app.routers import auth

app = FastAPI(title="CreatorPilot AI Backend")

# Updated CORS middleware allowing both port 5173 and 5174
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    close_mongo_connection()

@app.get("/")
def read_root():
    return {"status": "online", "message": "CreatorPilot AI Backend is running"}

app.include_router(auth.router, prefix="/api", tags=["Auth"])