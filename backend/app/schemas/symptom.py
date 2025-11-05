from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SymptomBase(BaseModel):
    name: str
    category: str
    description: Optional[str] = None
    severity_level: Optional[str] = None
    body_part: Optional[str] = None
    is_emergency: bool = False

class SymptomCreate(SymptomBase):
    pass

class Symptom(SymptomBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ConditionBase(BaseModel):
    name: str
    description: Optional[str] = None
    specialty: str
    urgency_level: str

class ConditionCreate(ConditionBase):
    pass

class Condition(ConditionBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class TriageRequest(BaseModel):
    symptoms: List[str]
    vitals: Optional[dict] = None  # {temperature: 98.6, heart_rate: 75, etc.}

class TriageResponse(BaseModel):
    possible_conditions: List[Condition]
    recommended_specialties: List[str]
    urgency_level: str
    recommended_doctors: List[dict]