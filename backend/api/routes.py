from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import uuid

from database.session import get_db
from services.monitoring_service import RealTimeMonitoringSession
from services.database_service import DatabaseService
from models.schemas import Patient

router = APIRouter(prefix="/api")
monitoring_sessions = {}

@router.get("/")
async def root():
    return {"message": "Real-Time Medical Kiosk API", "status": "running", "version": "3.1.0"}

@router.post("/sessions/start")
async def start_monitoring_session(
    patient_id: str = None,
    db: Session = Depends(get_db)
):
    session_id = str(uuid.uuid4())
    monitoring_session = RealTimeMonitoringSession(session_id, db, patient_id)
    monitoring_session.start()
    monitoring_sessions[session_id] = monitoring_session
    
    return {
        "session_id": session_id, 
        "message": "Real-time monitoring started",
        "patient_id": patient_id
    }

@router.post("/sessions/{session_id}/stop")
async def stop_monitoring_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    if session_id not in monitoring_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    monitoring_session = monitoring_sessions[session_id]
    monitoring_session.stop()
    del monitoring_sessions[session_id]
    
    return {"message": "Monitoring session stopped"}

@router.get("/sessions/{session_id}/data")
async def get_session_data(
    session_id: str,
    db: Session = Depends(get_db)
):
    database_service = DatabaseService(db)
    session_data = database_service.get_session_data(session_id)
    
    if not session_data["session"]:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session_data

@router.post("/patients")
async def create_patient(
    patient_id: str,
    name: str,
    age: int,
    gender: str,
    db: Session = Depends(get_db)
):
    database_service = DatabaseService(db)
    
    # Check if patient already exists
    existing_patient = database_service.get_patient_by_id(patient_id)
    if existing_patient:
        raise HTTPException(status_code=400, detail="Patient already exists")
    
    patient = database_service.create_patient(patient_id, name, age, gender)
    
    return {
        "message": "Patient created successfully",
        "patient": {
            "patient_id": patient.patient_id,
            "name": patient.name,
            "age": patient.age,
            "gender": patient.gender
        }
    }

@router.get("/patients/{patient_id}")
async def get_patient(patient_id: str, db: Session = Depends(get_db)):
    database_service = DatabaseService(db)
    patient = database_service.get_patient_by_id(patient_id)
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return {
        "patient_id": patient.patient_id,
        "name": patient.name,
        "age": patient.age,
        "gender": patient.gender,
        "created_at": patient.created_at
    }