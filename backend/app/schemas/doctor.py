from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DoctorBase(BaseModel):
    name: str
    specialty: str
    contact: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class DoctorCreate(DoctorBase):
    pass

class DoctorUpdate(DoctorBase):
    pass

class Doctor(DoctorBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DoctorList(BaseModel):
    doctors: list[Doctor]
    total: int