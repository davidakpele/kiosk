from api import routes
from api import websockets 
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(
    title="AI Medical Kiosk - SMOOTH REAL-TIME",
    version="3.1.0",
    description="Real-time medical kiosk with continuous smooth processing"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes directly
app.include_router(routes.router)
websockets.register_websocket_handlers(app)
# Serve static files (HTML, CSS, JS) - ADD THIS BACK
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# Health endpoints
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "3.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)