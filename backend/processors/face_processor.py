# processors/face_processor.py
import cv2
import numpy as np
import pickle
import os
import face_recognition
from typing import Dict, List, Optional
import json
import logging
import mediapipe as mp
from datetime import datetime

logger = logging.getLogger(__name__)

class FaceRecognitionService:
    def __init__(self, data_dir: str = "user_data"):
        self.data_dir = data_dir
        self.encodings_file = os.path.join(data_dir, "face_encodings.pkl")
        self.users_file = os.path.join(data_dir, "users.json")
        self.face_encodings = []
        self.face_users = []
        self.users = {}
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        os.makedirs(data_dir, exist_ok=True)
        self.load_user_data()
        
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
    
    def load_user_data(self):
        """Load existing face encodings and user data"""
        try:
            if os.path.exists(self.encodings_file):
                with open(self.encodings_file, 'rb') as f:
                    data = pickle.load(f)
                    self.face_encodings = data.get('encodings', [])
                    self.face_users = data.get('users', [])
            
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r') as f:
                    self.users = json.load(f)
                    
            logger.info(f"Loaded {len(self.face_users)} registered users")
        except Exception as e:
            logger.error(f"Error loading user data: {e}")
            self.face_encodings = []
            self.face_users = []
            self.users = {}
    
    def save_user_data(self):
        """Save face encodings and user data to files"""
        try:
            with open(self.encodings_file, 'wb') as f:
                pickle.dump({
                    'encodings': self.face_encodings,
                    'users': self.face_users
                }, f)
            
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving user data: {e}")
    
    def register_user(self, username: str, face_image: np.ndarray) -> Dict:
        """
        Register a new user with face recognition
        """
        try:
            # Check if username already exists
            if username in self.face_users:
                return {
                    'success': False,
                    'message': f'Username "{username}" already exists'
                }
            
            # Extract face encodings
            rgb_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_image)
            
            if not face_locations:
                return {
                    'success': False,
                    'message': 'No face detected in the image'
                }
            
            # Get face encoding
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
            
            if not face_encodings:
                return {
                    'success': False,
                    'message': 'Could not extract face features'
                }
            
            # Check if face already registered with strict tolerance
            matches = face_recognition.compare_faces(self.face_encodings, face_encodings[0], tolerance=0.5)
            if any(matches):
                return {
                    'success': False,
                    'message': 'This face is already registered'
                }
            
            # Register new user
            self.face_encodings.append(face_encodings[0])
            self.face_users.append(username)
            
            # Create simple user profile
            self.users[username] = {
                'username': username,
                'registration_date': datetime.now().isoformat(),
                'last_login': None
            }
            
            self.save_user_data()
            
            return {
                'success': True,
                'message': f'User "{username}" registered successfully',
                'username': username
            }
            
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return {
                'success': False,
                'message': f'Registration failed: {str(e)}'
            }
    
    def recognize_user(self, face_image: np.ndarray) -> Dict:
        """
        Recognize user from face image
        """
        try:
            if not self.face_encodings:
                return {
                    'success': False,
                    'message': 'No registered users found'
                }
            
            # Extract face encoding from current image
            rgb_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_image)
            
            if not face_locations:
                return {
                    'success': False,
                    'message': 'No face detected'
                }
            
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
            
            if not face_encodings:
                return {
                    'success': False,
                    'message': 'Could not extract face features'
                }
            
            # Compare with registered faces
            matches = face_recognition.compare_faces(
                self.face_encodings, 
                face_encodings[0], 
                tolerance=0.5
            )
            
            face_distances = face_recognition.face_distance(
                self.face_encodings, 
                face_encodings[0]
            )
            
            # Find best match
            best_match_index = np.argmin(face_distances) if face_distances.size > 0 else -1
            best_distance = face_distances[best_match_index] if best_match_index != -1 else float('inf')
            
            # Calculate confidence
            confidence = max(0, 1 - (best_distance / 0.6))
            
            # Only accept high confidence matches
            if best_match_index != -1 and matches[best_match_index] and confidence > 0.7:
                username = self.face_users[best_match_index]
                
                # Update last login
                self.users[username]['last_login'] = datetime.now().isoformat()
                self.save_user_data()
                
                return {
                    'success': True,
                    'username': username,
                    'user_data': self.users[username],
                    'confidence': round(confidence, 3),
                    'message': f'Welcome back {username}!'
                }
            else:
                return {
                    'success': False,
                    'message': 'User not recognized. Please register first.'
                }
                
        except Exception as e:
            logger.error(f"Error recognizing user: {e}")
            return {
                'success': False,
                'message': f'Recognition failed: {str(e)}'
            }
    
    def get_user_data(self, username: str) -> Optional[Dict]:
        """Get user data by username"""
        return self.users.get(username)
    
    def get_all_users(self) -> List[str]:
        """Get list of all registered usernames"""
        return self.face_users.copy()
    
    def delete_user(self, username: str) -> bool:
        """Delete user and their face data"""
        try:
            if username in self.face_users:
                index = self.face_users.index(username)
                self.face_users.pop(index)
                self.face_encodings.pop(index)
                
            if username in self.users:
                del self.users[username]
            
            self.save_user_data()
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user {username}: {e}")
            return False