# backend/app/services/live_camera.py
import cv2
import threading
import time
import base64
from typing import Optional, Callable

class LiveCameraSystem:
    def __init__(self):
        self.cap = None
        self.is_running = False
        self.current_frame = None
        self.face_detected = False
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.on_face_detected = None
        self.camera_thread = None
        
    def start_camera(self):
        """Start the live camera feed"""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise Exception("Cannot access camera")
            
            self.is_running = True
            self.camera_thread = threading.Thread(target=self._camera_loop)
            self.camera_thread.daemon = True
            self.camera_thread.start()
            return True
        except Exception as e:
            print(f"Camera error: {e}")
            return False
    
    def _camera_loop(self):
        """Main camera processing loop"""
        while self.is_running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                continue
            
            self.current_frame = frame
            
            # Detect faces in real-time
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(100, 100))
            
            # Update face detection status
            had_face = self.face_detected
            self.face_detected = len(faces) > 0
            
            # Trigger callback when face first appears
            if self.face_detected and not had_face and self.on_face_detected:
                self.on_face_detected(faces)
            
            # Draw face rectangles on frame
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, "FACE DETECTED", (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            time.sleep(0.03)  # ~30 FPS
    
    def get_live_frame(self) -> Optional[str]:
        """Get current camera frame as base64"""
        if self.current_frame is None:
            return None
        
        try:
            # Resize for performance
            frame = cv2.resize(self.current_frame, (640, 480))
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')
            return f"data:image/jpeg;base64,{jpg_as_text}"
        except Exception as e:
            print(f"Frame encoding error: {e}")
            return None
    
    def get_camera_status(self) -> dict:
        """Get current camera and face detection status"""
        return {
            "camera_active": self.is_running,
            "face_detected": self.face_detected,
            "frame_available": self.current_frame is not None
        }
    
    def wait_for_face(self, timeout: int = 30) -> bool:
        """Wait for a face to be detected"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.face_detected:
                return True
            time.sleep(0.5)
        return False
    
    def stop_camera(self):
        """Stop the camera"""
        self.is_running = False
        if self.cap:
            self.cap.release()
        if self.camera_thread:
            self.camera_thread.join(timeout=2.0)