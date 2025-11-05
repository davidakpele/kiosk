import cv2
import mediapipe as mp
import numpy as np
from typing import Dict, List, Tuple, Optional

class FaceProcessor:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Define regions of interest (ROI) indices
        self.cheek_indices = list(range(116, 150))  # Both cheeks
        self.forehead_indices = list(range(10, 30))  # Forehead
        self.face_oval_indices = list(range(10, 150))  # Full face for rPPG
        
    def process_frame(self, frame: np.ndarray) -> Dict:
        """Process frame to extract face landmarks and ROIs"""
        results = self.face_mesh.process(frame)
        output = {
            'landmarks': None,
            'rois': {},
            'bounding_box': None,
            'face_detected': False
        }
        
        if not results.multi_face_landmarks:
            return output
            
        landmarks = results.multi_face_landmarks[0]
        output['landmarks'] = landmarks
        output['face_detected'] = True
        
        # Convert landmarks to pixel coordinates
        h, w = frame.shape[:2]
        landmarks_array = np.array([(lm.x * w, lm.y * h) for lm in landmarks.landmark])
        
        # Extract ROIs
        output['rois'] = self._extract_rois(frame, landmarks_array)
        output['bounding_box'] = self._get_face_bounding_box(landmarks_array)
        
        return output
    
    def _extract_rois(self, frame: np.ndarray, landmarks: np.ndarray) -> Dict:
        """Extract regions of interest from face"""
        rois = {}
        
        # Full face ROI for rPPG
        face_pts = landmarks[self.face_oval_indices].astype(np.int32)
        x, y, w, h = cv2.boundingRect(face_pts)
        rois['face'] = frame[y:y+h, x:x+w]
        
        # Cheek ROIs
        cheek_pts = landmarks[self.cheek_indices].astype(np.int32)
        x_c, y_c, w_c, h_c = cv2.boundingRect(cheek_pts)
        rois['cheeks'] = frame[y_c:y_c+h_c, x_c:x_c+w_c]
        
        # Forehead ROI
        forehead_pts = landmarks[self.forehead_indices].astype(np.int32)
        x_f, y_f, w_f, h_f = cv2.boundingRect(forehead_pts)
        rois['forehead'] = frame[y_f:y_f+h_f, x_f:x_f+w_f]
        
        return rois
    
    def _get_face_bounding_box(self, landmarks: np.ndarray) -> Tuple:
        """Get bounding box around face"""
        x_min, y_min = np.min(landmarks, axis=0)
        x_max, y_max = np.max(landmarks, axis=0)
        return (int(x_min), int(y_min), int(x_max - x_min), int(y_max - y_min))
    
    def draw_landmarks(self, frame: np.ndarray, results: Dict) -> np.ndarray:
        """Draw face landmarks and ROIs on frame"""
        if not results['face_detected']:
            return frame
            
        annotated_frame = frame.copy()
        landmarks = results['landmarks']
        
        # Draw face mesh
        self.mp_drawing.draw_landmarks(
            image=annotated_frame,
            landmark_list=landmarks,
            connections=self.mp_face_mesh.FACEMESH_TESSELATION,
            landmark_drawing_spec=None,
            connection_drawing_spec=self.mp_drawing.DrawingSpec(
                color=(0, 255, 0), thickness=1, circle_radius=1
            )
        )
        
        # Draw bounding box
        x, y, w, h = results['bounding_box']
        cv2.rectangle(annotated_frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        
        return annotated_frame