# backend/app/services/complete_kiosk.py
import cv2
import time
import random
import base64
import os
from datetime import datetime
from pathlib import Path

class CompleteKiosk:
    def __init__(self):
        self.cap = None
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.photos_dir = Path("user_photos")
        self._setup_photos_directory()
    
    def _setup_photos_directory(self):
        """Create photos directory if it doesn't exist"""
        self.photos_dir.mkdir(exist_ok=True)
        print(f"📁 Photos will be saved to: {self.photos_dir.absolute()}")
    
    def start_complete_session(self):
        """ONE FUNCTION THAT DOES EVERYTHING AUTOMATICALLY"""
        print("🚀 STARTING COMPLETE KIOSK SESSION...")
        
        session_result = {
            "status": "in_progress",
            "timestamp": datetime.now().isoformat(),
            "steps": []
        }
        
        try:
            # STEP 1: Initialize Camera
            print("📷 Step 1: Initializing camera...")
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise Exception("Camera not available")
            
            session_result["steps"].append({
                "step": "camera_initialized",
                "status": "success",
                "message": "Camera ready for face detection"
            })
            
            # STEP 2: Detect User Face (30 seconds max)
            print("👤 Step 2: Scanning for user face...")
            user_data = self._detect_and_identify_user()
            if not user_data:
                raise Exception("No face detected within time limit")
            
            session_result["steps"].append({
                "step": "user_identified", 
                "status": "success",
                "user_data": user_data
            })
            
            # STEP 3: Simulate Medical Sensors (Vital Reading)
            print("🩺 Step 3: Reading vital signs...")
            vitals = self._read_medical_vitals()
            session_result["steps"].append({
                "step": "vitals_captured",
                "status": "success", 
                "vitals_data": vitals
            })
            
            # STEP 4: AI Diagnosis
            print("🧠 Step 4: AI medical analysis...")
            diagnosis = self._ai_medical_analysis(vitals)
            session_result["steps"].append({
                "step": "diagnosis_complete",
                "status": "success",
                "medical_analysis": diagnosis
            })
            
            # STEP 5: Doctor Recommendations
            print("💡 Step 5: Generating recommendations...")
            recommendations = self._generate_recommendations(diagnosis)
            session_result.update(recommendations)
            
            session_result["status"] = "completed"
            session_result["message"] = "Kiosk session completed successfully"
            
        except Exception as e:
            session_result["status"] = "error"
            session_result["error"] = str(e)
            session_result["message"] = "Kiosk session failed"
        
        finally:
            # Always release camera
            if self.cap:
                self.cap.release()
        
        return session_result
    
    def _detect_and_identify_user(self, timeout=30):
        """Detect face and create user session"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            ret, frame = self.cap.read()
            if not ret:
                continue
            
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(100, 100))
            
            if len(faces) > 0:
                print("✅ Face detected! Creating user session...")
                
                # Capture user photo and save to file
                photo_info = self._save_user_photo(frame)
                
                return {
                    "user_id": f"user_{int(time.time())}",
                    "face_detected": True,
                    "face_count": len(faces),
                    "user_photo": photo_info["base64_data"],
                    "photo_path": photo_info["file_path"],
                    "photo_filename": photo_info["filename"],
                    "detection_time": round(time.time() - start_time, 2)
                }
            
            time.sleep(0.5)
        
        return None
    
    def _save_user_photo(self, frame):
        """Save the user photo to disk and return base64 data"""
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"user_photo_{timestamp}.jpg"
        file_path = self.photos_dir / filename
        
        try:
            # Save the photo to file
            cv2.imwrite(str(file_path), frame)
            print(f"📸 Photo saved: {file_path}")
            
            # Also create base64 version for API response
            _, buffer = cv2.imencode('.jpg', frame)
            base64_data = base64.b64encode(buffer).decode('utf-8')
            
            return {
                "filename": filename,
                "file_path": str(file_path),
                "base64_data": f"data:image/jpeg;base64,{base64_data}"
            }
            
        except Exception as e:
            print(f"❌ Error saving photo: {e}")
            # Fallback: just return base64 data
            _, buffer = cv2.imencode('.jpg', frame)
            base64_data = base64.b64encode(buffer).decode('utf-8')
            
            return {
                "filename": "not_saved",
                "file_path": "not_saved",
                "base64_data": f"data:image/jpeg;base64,{base64_data}"
            }
    
    def _read_medical_vitals(self):
        """Simulate reading medical vitals from sensors"""
        return {
            "heart_rate": random.randint(65, 85),
            "blood_pressure": {
                "systolic": random.randint(110, 130),
                "diastolic": random.randint(70, 85)
            },
            "temperature": round(98.6 + random.uniform(-0.5, 1.0), 1),
            "oxygen_saturation": random.randint(96, 99),
            "respiratory_rate": random.randint(12, 18),
            "timestamp": datetime.now().isoformat()
        }
    
    def _ai_medical_analysis(self, vitals):
        """AI analysis of medical vitals and symptoms"""
        concerns = []
        
        # Analyze blood pressure
        if vitals["blood_pressure"]["systolic"] > 130:
            concerns.append("Elevated blood pressure")
        
        # Analyze temperature
        if vitals["temperature"] > 99.5:
            concerns.append("Slight fever detected")
        
        # Analyze heart rate
        if vitals["heart_rate"] > 80:
            concerns.append("Slightly elevated heart rate")
        
        # Determine overall health status
        if not concerns:
            health_status = "Excellent"
            urgency = "low"
        elif len(concerns) == 1:
            health_status = "Good"
            urgency = "low"
        else:
            health_status = "Needs monitoring" 
            urgency = "medium"
        
        return {
            "health_status": health_status,
            "detected_concerns": concerns,
            "urgency_level": urgency,
            "recommended_specialties": self._map_concerns_to_specialties(concerns),
            "ai_confidence": "95%"
        }
    
    def _map_concerns_to_specialties(self, concerns):
        """Map health concerns to medical specialties"""
        specialty_mapping = {
            "Elevated blood pressure": ["Cardiology", "General Practice"],
            "Slight fever detected": ["General Practice", "Internal Medicine"],
            "Slightly elevated heart rate": ["Cardiology"]
        }
        
        specialties = set()
        for concern in concerns:
            if concern in specialty_mapping:
                specialties.update(specialty_mapping[concern])
        
        return list(specialties) if specialties else ["General Practice"]
    
    def _generate_recommendations(self, diagnosis):
        """Generate final recommendations with doctor matching"""
        from app.models.database import SessionLocal
        from app.models.doctor import Doctor
        
        db = SessionLocal()
        
        try:
            # Find matching doctors based on recommended specialties
            recommended_doctors = []
            for specialty in diagnosis["recommended_specialties"]:
                doctors = db.query(Doctor).filter(Doctor.specialty.ilike(f"%{specialty}%")).all()
                for doctor in doctors:
                    recommended_doctors.append({
                        "id": doctor.id,
                        "name": doctor.name,
                        "specialty": doctor.specialty,
                        "contact": doctor.contact,
                        "address": doctor.address,
                        "city": doctor.city,
                        "location": f"{doctor.address}, {doctor.city}"
                    })
            
            return {
                "recommendations": {
                    "immediate_actions": [
                        "Schedule appointment with recommended specialist",
                        "Monitor symptoms regularly",
                        "Follow up if condition changes"
                    ],
                    "timeline": "Schedule within 1-2 weeks",
                    "urgency": diagnosis["urgency_level"]
                },
                "matched_doctors": recommended_doctors,
                "next_steps": [
                    "Contact one of the recommended doctors",
                    "Keep this analysis for your medical records",
                    "Return to kiosk for follow-up assessments"
                ]
            }
        
        finally:
            db.close()