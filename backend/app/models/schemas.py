from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from app.database.session import Base
from datetime import datetime

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(String, default="active")
    patient_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class PhysiologicalData(Base):
    __tablename__ = "physiological_data"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    heart_rate = Column(Float)
    stress_index = Column(Float)
    confidence = Column(Float)
    alerts = Column(JSON)
    face_detected = Column(Boolean, default=False)

class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    analysis_type = Column(String)
    result = Column(JSON)
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, unique=True, index=True)
    name = Column(String)
    age = Column(Integer)
    gender = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)