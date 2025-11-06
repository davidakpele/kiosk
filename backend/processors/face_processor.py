import cv2
import numpy as np
import mediapipe as mp
from typing import Dict, Optional

class FastFaceProcessor:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
    def process_frame(self, frame) -> Dict:
        results = self.face_mesh.process(frame)
        face_detected = False
        landmarks = None
        
        if results.multi_face_landmarks:
            face_detected = True
            landmarks = results.multi_face_landmarks[0]
            
        return {
            'face_detected': face_detected,
            'landmarks': landmarks
        }
    
    def draw_landmarks(self, frame, landmarks):
        if not landmarks:
            return frame
            
        h, w = frame.shape[:2]
        for landmark in landmarks.landmark:
            x, y = int(landmark.x * w), int(landmark.y * h)
            cv2.circle(frame, (x, y), 1, (255, 0, 0), -1)
        return frame