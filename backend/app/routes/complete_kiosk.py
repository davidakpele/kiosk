# backend/app/routes/complete_kiosk.py
from datetime import datetime
from http.client import HTTPException
from pathlib import Path
from fastapi import APIRouter
from app.services.complete_kiosk import CompleteKiosk

router = APIRouter(prefix="/kiosk", tags=["kiosk"])

@router.get("/start-session")
def start_complete_kiosk_session():
    """
    SINGLE ENDPOINT - COMPLETE KIOSK EXPERIENCE
    Turns on camera → Detects user → Reads vitals → AI diagnosis → Doctor recommendations
    """
    kiosk = CompleteKiosk()
    result = kiosk.start_complete_session()
    return result

# Add this to your routes
@router.get("/user-photos")
def list_user_photos():
    """List all saved user photos"""
    photos_dir = Path("user_photos")
    photos = []
    
    if photos_dir.exists():
        for file in photos_dir.glob("user_photo_*.jpg"):
            photos.append({
                "filename": file.name,
                "file_path": str(file),
                "size": file.stat().st_size,
                "created": datetime.fromtimestamp(file.stat().st_ctime).isoformat()
            })
    
    return {"photos": photos}

@router.delete("/user-photos/{filename}")
def delete_user_photo(filename: str):
    """Delete a specific user photo"""
    photos_dir = Path("user_photos")
    file_path = photos_dir / filename
    
    # Security check to prevent path traversal
    if not file_path.exists() or ".." in filename:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    file_path.unlink()
    return {"message": f"Photo {filename} deleted successfully"}