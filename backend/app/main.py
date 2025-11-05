from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import doctors, complete_kiosk  

app = FastAPI(
    title="AI Medical Kiosk - LIVE CAMERA",
    version="3.0.0",
    description="Real-time medical kiosk with live camera processing"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(doctors.router)
app.include_router(complete_kiosk.router)

@app.get("/")
async def root():
    return {
        "message": "LIVE AI Medical Kiosk Running!",
        "version": "3.0.0",
        "features": [
            "Real-time camera processing",
            "Live face detection", 
            "Instant health assessment",
            "No static data - everything live"
        ]
    }