# backend/app/routes/realtime_kiosk.py
from fastapi import APIRouter, BackgroundTasks
from app.services.realtime_kiosk import RealTimeKiosk

router = APIRouter(prefix="/realtime", tags=["realtime-kiosk"])

# Global kiosk instance
kiosk = RealTimeKiosk()

@router.get("/start-session")
def start_realtime_session():
    """Start real-time kiosk session with LIVE camera"""
    result = kiosk.start_realtime_session()
    return result

@router.get("/live-status")
def get_live_status():
    """Get real-time camera status and live video frame"""
    return kiosk.get_live_status()

@router.post("/wait-for-user")
def wait_for_user():
    """Wait for user to appear in camera"""
    return kiosk.wait_for_user(timeout=60)

@router.post("/capture-user")
def capture_user_data():
    """Capture user data once detected"""
    return kiosk.capture_user_session()

@router.post("/health-assessment")
def perform_health_assessment():
    """Perform real-time health assessment"""
    return kiosk.process_health_assessment()

@router.post("/complete-session")
def complete_kiosk_session():
    """Complete the entire kiosk session"""
    return kiosk.complete_session()

@router.post("/stop-session")
def stop_session():
    """Force stop the session"""
    return kiosk.stop_session()