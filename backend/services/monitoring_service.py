import base64
import cv2
import time
from datetime import datetime
from typing import Dict, Optional
from sqlalchemy.orm import Session
import asyncio

from processors.camera import FastCamera
from processors.face_processor import FaceRecognitionService
from processors.rppg_processor import FastRPPGProcessor
from services.diagnosis_service import RealTimeMedicalDiagnosis
from services.database_service import DatabaseService

class RealTimeMonitoringSession:
    def __init__(self, session_id: str, db: Session, patient_id: Optional[str] = None):
        self.session_id = session_id
        self.patient_id = patient_id
        self.db = db
        self.database_service = DatabaseService(db)
        
        self.camera = FastCamera()
        self.face_processor = FaceRecognitionService()
        self.rppg_processor = FastRPPGProcessor()
        self.diagnosis = RealTimeMedicalDiagnosis()
        
        self.is_running = False
        self.frame_count = 0
        self.last_diagnosis = None
        self.ai_update_counter = 0
        self.last_ai_update_time = 0
        
    def start(self):
        if not self.camera.initialize():
            raise Exception("Could not initialize camera")
        
        # Create database session record
        self.database_service.create_session(self.session_id, self.patient_id)
        self.is_running = True
        
    def stop(self):
        self.is_running = False
        # End database session
        self.database_service.end_session(self.session_id)
        if self.camera:
            self.camera.release()
            
    async def process_frame(self) -> Optional[Dict]:
        """Async frame processing that doesn't block on AI calls"""
        if not self.is_running:
            return None
            
        frame = self.camera.get_frame()
        if frame is None:
            return None
        
        face_results = self.face_processor.process_frame(frame)
        
        diagnosis_result = self.last_diagnosis
        
        if face_results['face_detected']:
            signal_value = self.rppg_processor.extract_signal(frame, face_results['landmarks'])
            if signal_value > 0:
                self.rppg_processor.add_signal(signal_value)

                if self.frame_count % 15 == 0 and len(self.rppg_processor.signal_buffer) >= 30:
                    bpm, confidence = self.rppg_processor.compute_heart_rate()
                    if bpm > 0:
                        diagnosis_result = self.diagnosis.analyze_vitals(bpm, confidence)
                        self.last_diagnosis = diagnosis_result
                        if diagnosis_result and diagnosis_result['heart_rate'] > 0:
                            self.database_service.save_physiological_data(
                                session_id=self.session_id,
                                heart_rate=diagnosis_result['heart_rate'],
                                stress_index=diagnosis_result['stress_level'],
                                confidence=diagnosis_result['confidence'],
                                alerts=diagnosis_result['alerts'],
                                face_detected=face_results['face_detected']
                            )
        
        self.frame_count += 1
    
        current_time = time.time()
        if (current_time - self.last_ai_update_time > 10 and 
            diagnosis_result and 
            diagnosis_result['heart_rate'] > 0):
            
            self.last_ai_update_time = current_time
            self.ai_update_counter += 1
            asyncio.create_task(self._update_ai_advice_async(diagnosis_result))
        
        if face_results['face_detected'] and face_results['landmarks']:
            frame = self.fast_draw_landmarks(frame, face_results['landmarks'])
        
        if diagnosis_result:
            frame = self.fast_add_overlay(frame, diagnosis_result)
        
        _, buffer = cv2.imencode('.jpg', cv2.cvtColor(frame, cv2.COLOR_RGB2BGR), 
                               [cv2.IMWRITE_JPEG_QUALITY, 85])
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return {
            'frame': frame_base64,
            'timestamp': datetime.now().isoformat(),
            'diagnosis': diagnosis_result,
            'face_detected': face_results['face_detected'],
            'frame_count': self.frame_count,
            'processing_mode': 'realtime_continuous',
            'session_id': self.session_id,
            'patient_id': self.patient_id,
            'ai_update_count': self.ai_update_counter
        }
    
    async def _update_ai_advice_async(self, diagnosis_result: Dict):
        """Update AI advice asynchronously without blocking the main loop"""
        try:
            new_advice = await self.diagnosis.get_ai_medical_advice_async(diagnosis_result)

            self.diagnosis.update_ai_advice(new_advice)
            if self.last_diagnosis:
                self.last_diagnosis['ai_advice'] = new_advice
                
        except Exception as e:
            print(f"Async AI update error: {e}")
    
    def fast_draw_landmarks(self, frame, landmarks):
        """Draw face landmarks in green color"""
        h, w = frame.shape[:2]
        for landmark in landmarks.landmark:
            x, y = int(landmark.x * w), int(landmark.y * h)
            cv2.circle(frame, (x, y), 2, (0, 255, 0), -1) 
        return frame
    
    def fast_add_overlay(self, frame, diagnosis):
        """Add overlay with health information"""
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (350, 130), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)
        
        texts = [
            f"HR: {diagnosis['heart_rate']} BPM",
            f"Stress: {diagnosis['stress_level']}",
            f"Status: {diagnosis['health_status']}",
        ]
        
        for i, text in enumerate(texts):
            color = (0, 255, 0) if diagnosis['health_status'] == 'Normal' else (0, 165, 255)
            cv2.putText(frame, text, (15, 35 + i * 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)
        
        return frame