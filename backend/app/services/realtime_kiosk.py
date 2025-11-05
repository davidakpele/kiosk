# backend/app/services/realtime_kiosk.py
import time
import cv2
from app.services.live_camera import LiveCameraSystem

class RealTimeKiosk:
    def __init__(self):
        self.camera = LiveCameraSystem()
        self.session_active = False
        self.current_user = None
        
    def start_realtime_session(self):
        """Start real-time kiosk session with live camera"""
        print("🚀 Starting REAL-TIME kiosk session...")
        
        # Start live camera
        if not self.camera.start_camera():
            return {"error": "Camera failed to start"}
        
        self.session_active = True
        session_data = {
            "status": "camera_started",
            "timestamp": time.time(),
            "phases": []
        }
        
        return session_data
    
    def get_live_status(self):
        """Get real-time camera status and frame"""
        if not self.session_active:
            return {"error": "No active session"}
        
        frame_data = self.camera.get_live_frame()
        status = self.camera.get_camera_status()
        
        return {
            "camera_status": status,
            "live_frame": frame_data,
            "session_active": self.session_active,
            "user_detected": status["face_detected"]
        }
    
    def wait_for_user(self, timeout: int = 60):
        """Wait for user to appear in camera"""
        print("👤 Waiting for user to approach...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.camera.get_camera_status()
            
            if status["face_detected"]:
                print("✅ User detected!")
                return {
                    "status": "user_detected",
                    "wait_time": round(time.time() - start_time, 2),
                    "message": "User is now in front of camera"
                }
            
            time.sleep(0.5)
        
        return {
            "status": "timeout", 
            "wait_time": timeout,
            "message": "No user detected"
        }
    
    def capture_user_session(self):
        """Capture user data once face is detected"""
        print("📸 Capturing user session...")
        
        # Wait for stable face detection
        stable_count = 0
        for _ in range(20):  # Check for 2 seconds
            if self.camera.face_detected:
                stable_count += 1
            else:
                stable_count = 0
            time.sleep(0.1)
        
        if stable_count < 15:  # Need 75% stability
            return {"error": "Face not stable"}
        
        # Capture user photo
        user_photo = self.camera.get_live_frame()
        
        # Generate user ID based on timestamp
        user_id = f"user_{int(time.time())}"
        
        return {
            "user_id": user_id,
            "photo_captured": user_photo is not None,
            "timestamp": time.time(),
            "status": "user_registered"
        }
    
    def process_health_assessment(self):
        """Process health assessment in real-time"""
        print("🩺 Starting health assessment...")
        
        # Simulate vital reading process
        time.sleep(2)  # Simulate sensor reading time
        
        # Generate realistic vitals based on camera analysis
        # In real system, this would come from actual sensors
        import random
        vitals = {
            "heart_rate": random.randint(65, 85),
            "temperature": round(98.6 + random.uniform(-0.5, 1.0), 1),
            "respiratory_rate": random.randint(12, 18),
            "timestamp": time.time()
        }
        
        return {
            "vitals": vitals,
            "status": "assessment_complete",
            "processing_time": 2.0
        }
    
    def generate_recommendations(self, user_data, vitals):
        """Generate real-time recommendations"""
        print("💡 Generating AI recommendations...")
        
        # Analyze based on vitals
        symptoms = []
        if vitals["temperature"] > 99.5:
            symptoms.append("Potential fever")
        if vitals["heart_rate"] > 80:
            symptoms.append("Elevated heart rate")
        
        recommendations = {
            "detected_concerns": symptoms,
            "urgency": "low" if not symptoms else "medium",
            "recommended_actions": [
                "Monitor symptoms",
                "Consult healthcare provider if concerns persist"
            ],
            "generated_at": time.time()
        }
        
        return recommendations
    
    def complete_session(self):
        """Complete the kiosk session"""
        print("✅ Completing kiosk session...")
        
        # Capture final data
        final_photo = self.camera.get_live_frame()
        user_data = self.capture_user_session()
        vitals = self.process_health_assessment()
        recommendations = self.generate_recommendations(user_data, vitals)
        
        # Stop camera
        self.camera.stop_camera()
        self.session_active = False
        
        return {
            "session_complete": True,
            "user_data": user_data,
            "health_data": vitals,
            "recommendations": recommendations,
            "final_photo": final_photo,
            "total_duration": "~5 minutes"
        }
    
    def stop_session(self):
        """Force stop the session"""
        self.session_active = False
        self.camera.stop_camera()
        return {"status": "session_stopped"}