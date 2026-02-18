from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

load_dotenv()

from routes import auth, weddings, credits, admins

# Database client
db_client = None
db = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_client, db
    # Startup
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.getenv("DATABASE_NAME", "wedding_platform")
    db_client = AsyncIOMotorClient(mongo_url)
    db = db_client[db_name]
    app.state.db = db
    print(f"Connected to MongoDB: {db_name}")
    
    yield
    
    # Shutdown
    if db_client:
        db_client.close()
        print("MongoDB connection closed")

app = FastAPI(title="Wedding Platform API", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "wedding-platform"}

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(admins.router, prefix="/api/admins", tags=["Admins"])
app.include_router(weddings.router, prefix="/api/weddings", tags=["Weddings"])
app.include_router(credits.router, prefix="/api/credits", tags=["Credits"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)