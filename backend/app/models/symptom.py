from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from .database import Base

class Symptom(Base):
    __tablename__ = "symptoms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    category = Column(String(50), nullable=False)  # cardiac, respiratory, neurological, etc.
    description = Column(Text)
    severity_level = Column(String(20))  # low, medium, high
    body_part = Column(String(50))  # head, chest, abdomen, etc.
    is_emergency = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Condition(Base):
    __tablename__ = "conditions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    specialty = Column(String(50), nullable=False)  # cardiology, neurology, etc.
    urgency_level = Column(String(20))  # low, medium, high, emergency
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SymptomConditionMapping(Base):
    __tablename__ = "symptom_condition_mapping"
    
    id = Column(Integer, primary_key=True, index=True)
    symptom_id = Column(Integer, nullable=False)
    condition_id = Column(Integer, nullable=False)
    confidence_score = Column(Integer)  # 1-100 scale
    created_at = Column(DateTime(timezone=True), server_default=func.now())