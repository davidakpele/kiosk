from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.database import get_db
from app.models.doctor import Doctor
from app.schemas.doctor import Doctor as DoctorSchema, DoctorList

router = APIRouter(prefix="/doctors", tags=["doctors"])

@router.get("/", response_model=DoctorList)
def get_doctors(
    skip: int = 0,
    limit: int = 100,
    specialty: Optional[str] = None,
    city: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all doctors with optional filtering"""
    query = db.query(Doctor)
    
    if specialty:
        query = query.filter(Doctor.specialty.ilike(f"%{specialty}%"))
    if city:
        query = query.filter(Doctor.city.ilike(f"%{city}%"))
    
    total = query.count()
    doctors = query.offset(skip).limit(limit).all()
    
    return DoctorList(doctors=doctors, total=total)

@router.get("/{doctor_id}", response_model=DoctorSchema)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    """Get a specific doctor by ID"""
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor

@router.get("/specialty/{specialty}", response_model=DoctorList)
def get_doctors_by_specialty(specialty: str, db: Session = Depends(get_db)):
    """Get doctors by specialty"""
    doctors = db.query(Doctor).filter(Doctor.specialty.ilike(f"%{specialty}%")).all()
    return DoctorList(doctors=doctors, total=len(doctors))