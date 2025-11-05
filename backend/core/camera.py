import cv2
import numpy as np
from typing import Optional, Tuple

class Camera:
    def __init__(self, resolution: Tuple[int, int] = (1280, 720)):
        self.resolution = resolution
        self.cap = None
        
    def initialize(self) -> bool:
        """Initialize camera with specified resolution"""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            return False
            
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        return True
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Capture frame from camera"""
        if self.cap is None:
            return None
            
        ret, frame = self.cap.read()
        if ret:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return None
    
    def release(self):
        """Release camera resources"""
        if self.cap:
            self.cap.release()