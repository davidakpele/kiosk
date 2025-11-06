from sqlalchemy.orm import Session
from datetime import datetime
from models.schemas import Session as DBSession, PhysiologicalData, AnalysisResult, Patient
from typing import Dict, List, Optional

class DatabaseService:
    def __init__(self, db: Session):
        self.db = db

    def create_session(self, session_id: str, patient_id: Optional[str] = None) -> DBSession:
        db_session = DBSession(
            session_id=session_id,
            patient_id=patient_id,
            start_time=datetime.utcnow(),
            status="active"
        )
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        return db_session

    def end_session(self, session_id: str):
        db_session = self.db.query(DBSession).filter(DBSession.session_id == session_id).first()
        if db_session:
            db_session.end_time = datetime.utcnow()
            db_session.status = "completed"
            self.db.commit()

    def save_physiological_data(self, session_id: str, heart_rate: float, 
                              stress_index: float, confidence: float, 
                              alerts: List[str], face_detected: bool):
        physiological_data = PhysiologicalData(
            session_id=session_id,
            heart_rate=heart_rate,
            stress_index=stress_index,
            confidence=confidence,
            alerts=alerts,
            face_detected=face_detected,
            timestamp=datetime.utcnow()
        )
        self.db.add(physiological_data)
        self.db.commit()

    def save_analysis_result(self, session_id: str, analysis_type: str, 
                           result: Dict, confidence: float):
        analysis_result = AnalysisResult(
            session_id=session_id,
            analysis_type=analysis_type,
            result=result,
            confidence=confidence,
            created_at=datetime.utcnow()
        )
        self.db.add(analysis_result)
        self.db.commit()

    def get_patient_by_id(self, patient_id: str) -> Optional[Patient]:
        return self.db.query(Patient).filter(Patient.patient_id == patient_id).first()

    def create_patient(self, patient_id: str, name: str, age: int, gender: str) -> Patient:
        patient = Patient(
            patient_id=patient_id,
            name=name,
            age=age,
            gender=gender
        )
        self.db.add(patient)
        self.db.commit()
        self.db.refresh(patient)
        return patient

    def get_session_data(self, session_id: str) -> Dict:
        session = self.db.query(DBSession).filter(DBSession.session_id == session_id).first()
        physiological_data = self.db.query(PhysiologicalData)\
            .filter(PhysiologicalData.session_id == session_id)\
            .order_by(PhysiologicalData.timestamp.desc())\
            .limit(100)\
            .all()
        analysis_results = self.db.query(AnalysisResult)\
            .filter(AnalysisResult.session_id == session_id)\
            .all()
        
        return {
            "session": session,
            "physiological_data": physiological_data,
            "analysis_results": analysis_results
        }