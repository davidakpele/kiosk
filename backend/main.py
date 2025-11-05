from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import json
import asyncio
import base64
import cv2
import numpy as np
import mediapipe as mp
from collections import deque
from scipy import signal
from scipy.fft import fft, fftfreq
from config import settings
from typing import Dict, List, Optional
import uuid
from datetime import datetime
import time

app = FastAPI(
    title="AI Medical Kiosk - SMOOTH REAL-TIME",
    version="3.1.0",
    description="Real-time medical kiosk with continuous smooth processing"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

monitoring_sessions: Dict[str, Dict] = {}

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
        
    def process_frame(self, frame):
        # Fast face detection - minimal processing
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

class FastRPPGProcessor:
    def __init__(self, fps=30, window_size=120):  # Smaller window for faster response
        self.fps = fps
        self.window_size = window_size
        self.signal_buffer = deque(maxlen=window_size)
        self.b, self.a = signal.butter(2, [0.8, 3.0], btype='bandpass', fs=fps)  # Faster filter
        
    def extract_signal(self, frame, landmarks):
        if not landmarks:
            return 0
            
        h, w = frame.shape[:2]
        landmarks_array = np.array([(lm.x * w, lm.y * h) for lm in landmarks.landmark])
        
        # Use minimal forehead points for speed
        forehead_indices = [10, 67, 108, 151, 337, 332]  # Reduced points
        forehead_pts = landmarks_array[forehead_indices].astype(np.int32)
        
        x, y, w, h = cv2.boundingRect(forehead_pts)
        if w > 0 and h > 0 and x + w < frame.shape[1] and y + h < frame.shape[0]:
            roi = frame[y:y+h, x:x+w]
            if roi.size > 0:
                return np.mean(roi[:, :, 1])  # Green channel
        
        return 0
    
    def add_signal(self, signal_value):
        self.signal_buffer.append(signal_value)
    
    def compute_heart_rate(self):
        if len(self.signal_buffer) < 40:  # Smaller minimum for faster response
            return 0, 0
        
        signal_array = np.array(self.signal_buffer)
        
        try:
            # Fast processing
            signal_detrended = signal.detrend(signal_array)
            signal_filtered = signal.filtfilt(self.b, self.a, signal_detrended)
            
            # Fast FFT
            fft_result = fft(signal_filtered)
            frequencies = fftfreq(len(signal_filtered), 1.0 / self.fps)
            
            positive_freq = frequencies[frequencies > 0]
            magnitude = np.abs(fft_result[frequencies > 0])
            
            hr_mask = (positive_freq >= 0.8) & (positive_freq <= 3.0)
            if not np.any(hr_mask):
                return 0, 0
            
            hr_freq = positive_freq[hr_mask]
            hr_magnitude = magnitude[hr_mask]
            
            peak_idx = np.argmax(hr_magnitude)
            bpm = hr_freq[peak_idx] * 60.0
            confidence = min(hr_magnitude[peak_idx] / np.mean(magnitude), 1.0)
            
            return bpm, confidence

        except:
            return 0, 0

class RealTimeMedicalDiagnosis:
    def __init__(self):
        self.bpm_history = deque(maxlen=15)  # Smaller history for faster response
        self.stress_history = deque(maxlen=15)
        self.last_update_time = time.time()
        
    def analyze_vitals(self, bpm, confidence):
        if bpm == 0 or confidence < 0.2:  # Lower threshold for more data
            return {
                'heart_rate': 0,
                'stress_level': 0,
                'fatigue_risk': 'Unknown',
                'health_status': 'No data',
                'alerts': ['Detecting face...'],
                'confidence': 0
            }
        
        # Update more frequently
        self.bpm_history.append(bpm)
        stress_level = 1.0 - min(confidence, 1.0)
        self.stress_history.append(stress_level)
        
        # Fast medical analysis
        alerts = []
        health_status = "Normal"
        fatigue_risk = "Low"
        
        # Quick heart rate analysis
        if bpm > 100:
            alerts.append("Elevated heart rate")
            health_status = "Warning"
        elif bpm < 50:
            alerts.append("Low heart rate")
            health_status = "Warning"
        else:
            alerts.append("Normal heart rate")
        
        # Quick stress analysis
        avg_stress = np.mean(list(self.stress_history)) if self.stress_history else 0
        if avg_stress > 0.7:
            alerts.append("High stress")
            fatigue_risk = "High"
        elif avg_stress > 0.5:
            alerts.append("Moderate stress")
            fatigue_risk = "Medium"
        else:
            alerts.append("Low stress")
        
        # Quick fatigue detection
        if len(self.bpm_history) >= 8:
            recent_avg = np.mean(list(self.bpm_history)[-4:])
            earlier_avg = np.mean(list(self.bpm_history)[-8:-4])
            if earlier_avg - recent_avg > 8:
                alerts.append("Possible fatigue")
                fatigue_risk = "High"
        
        return {
            'heart_rate': round(bpm, 1),
            'stress_level': round(avg_stress, 2),
            'fatigue_risk': fatigue_risk,
            'health_status': health_status,
            'alerts': alerts,
            'confidence': round(confidence, 2),
            'update_count': len(self.bpm_history)
        }

class FastCamera:
    def __init__(self, resolution=(1280, 720)):
        self.resolution = resolution
        self.cap = None
        
    def initialize(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            return False
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        return True
    
    def get_frame(self):
        if self.cap is None:
            return None
        ret, frame = self.cap.read()
        if ret:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return None
    
    def release(self):
        if self.cap:
            self.cap.release()

class RealTimeMonitoringSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.camera = FastCamera()
        self.face_processor = FastFaceProcessor()
        self.rppg_processor = FastRPPGProcessor()
        self.diagnosis = RealTimeMedicalDiagnosis()
        self.is_running = False
        self.frame_count = 0
        self.last_diagnosis = None
        
    def start(self):
        if not self.camera.initialize():
            raise Exception("Could not initialize camera")
        self.is_running = True
        
    def stop(self):
        self.is_running = False
        if self.camera:
            self.camera.release()
            
    def process_frame(self):
        if not self.is_running:
            return None
            
        frame = self.camera.get_frame()
        if frame is None:
            return None
        
        # Process face detection EVERY FRAME (no skipping)
        face_results = self.face_processor.process_frame(frame)
        
        diagnosis_result = self.last_diagnosis  # Use last result while computing
        
        # CONTINUOUS processing - no frame skipping
        if face_results['face_detected']:
            # Extract signal EVERY FRAME for continuous data
            signal_value = self.rppg_processor.extract_signal(frame, face_results['landmarks'])
            if signal_value > 0:
                self.rppg_processor.add_signal(signal_value)
                
                # Compute heart rate MORE FREQUENTLY (every 15 frames = 0.5 seconds)
                if self.frame_count % 15 == 0 and len(self.rppg_processor.signal_buffer) >= 30:
                    bpm, confidence = self.rppg_processor.compute_heart_rate()
                    if bpm > 0:
                        diagnosis_result = self.diagnosis.analyze_vitals(bpm, confidence)
                        self.last_diagnosis = diagnosis_result
        
        self.frame_count += 1
        
        # Fast visualization
        if face_results['face_detected'] and face_results['landmarks']:
            frame = self.fast_draw_landmarks(frame, face_results['landmarks'])
        
        if diagnosis_result:
            frame = self.fast_add_overlay(frame, diagnosis_result)
        
        # Fast encoding with lower quality for speed
        _, buffer = cv2.imencode('.jpg', cv2.cvtColor(frame, cv2.COLOR_RGB2BGR), 
                               [cv2.IMWRITE_JPEG_QUALITY, 85])
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return {
            'frame': frame_base64,
            'timestamp': datetime.now().isoformat(),
            'diagnosis': diagnosis_result,
            'face_detected': face_results['face_detected'],
            'frame_count': self.frame_count,
            'processing_mode': 'realtime_continuous'
        }
    
    def fast_draw_landmarks(self, frame, landmarks):
        h, w = frame.shape[:2]
        for landmark in landmarks.landmark:
            x, y = int(landmark.x * w), int(landmark.y * h)
            cv2.circle(frame, (x, y), 1, (255, 0, 0), -1)  # 🔵 Blue instead of green
        return frame
    
    def fast_add_overlay(self, frame, diagnosis):
        """Fast overlay with minimal text"""
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (350, 130), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)
        
        # Minimal text for speed
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

@app.get("/")
async def root():
    return {"message": "Real-Time Medical Kiosk API", "status": "running", "version": "3.1.0"}

@app.post("/api/sessions/start")
async def start_monitoring_session():
    session_id = str(uuid.uuid4())
    monitoring_session = RealTimeMonitoringSession(session_id)
    monitoring_session.start()
    monitoring_sessions[session_id] = monitoring_session
    return {"session_id": session_id, "message": "Real-time monitoring started"}

@app.post("/api/sessions/{session_id}/stop")
async def stop_monitoring_session(session_id: str):
    if session_id not in monitoring_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    monitoring_session = monitoring_sessions[session_id]
    monitoring_session.stop()
    del monitoring_sessions[session_id]
    return {"message": "Monitoring session stopped"}

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    if session_id not in monitoring_sessions:
        await websocket.close(code=1008, reason="Session not found")
        return
        
    monitoring_session = monitoring_sessions[session_id]
    await websocket.accept()
    
    try:
        while monitoring_session.is_running:
            start_time = time.time()
            
            # Continuous processing - no blocking
            result = monitoring_session.process_frame()
            
            if result:
                await websocket.send_json(result)
            
            # Maintain smooth 30 FPS with precise timing
            processing_time = time.time() - start_time
            sleep_time = max(0.001, (1/30) - processing_time)
            
            await asyncio.sleep(sleep_time)
            
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        print(f"Error in WebSocket: {e}")
    finally:
        await websocket.close()

# Your HTML endpoint remains exactly the same - it will work much better now!

@app.get("/monitor", response_class=HTMLResponse)
async def get_monitor_page():
    return """
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Medical Kiosk - LIVE DIAGNOSIS</title>
    <style>
        :root {
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --secondary: #64748b;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --dark: #1e293b;
            --light: #f8fafc;
            --border: #e2e8f0;
            --sidebar-width: 280px;
            --navbar-height: 70px;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f1f5f9;
            color: var(--dark);
            line-height: 1.6;
        }
        
        /* Top Navbar */
        .top-navbar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: var(--navbar-height);
            background: white;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 1.5rem;
            z-index: 1000;
        }
        
        .nav-left {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .menu-toggle {
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
            border-radius: 8px;
        }
        
        .menu-toggle:hover {
            background: #f1f5f9;
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .logo-icon {
            background: var(--primary);
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }
        
        .logo-text {
            font-weight: 700;
            font-size: 1.25rem;
        }
        
        .nav-right {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .user-menu {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .user-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: var(--primary);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }
        
        /* App Container */
        .app-container {
            display: flex;
            min-height: 100vh;
            padding-top: var(--navbar-height);
        }
        
        /* Sidebar */
        .sidebar {
            width: var(--sidebar-width);
            background: white;
            border-right: 1px solid var(--border);
            padding: 1.5rem;
            position: fixed;
            height: calc(100vh - var(--navbar-height));
            overflow-y: auto;
            transition: transform 0.3s ease;
            z-index: 999;
        }
        
        .sidebar.hidden {
            transform: translateX(-100%);
        }
        
        .nav-section {
            margin-bottom: 2rem;
        }
        
        .nav-title {
            font-size: 0.75rem;
            text-transform: uppercase;
            color: var(--secondary);
            margin-bottom: 0.75rem;
            font-weight: 600;
        }
        
        .nav-item {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.75rem;
            border-radius: 8px;
            margin-bottom: 0.25rem;
            cursor: pointer;
            transition: all 0.2s;
            text-decoration: none;
            color: var(--dark);
        }
        
        .nav-item:hover, .nav-item.active {
            background: var(--primary);
            color: white;
        }
        
        .nav-item i {
            width: 20px;
            text-align: center;
        }
        
        /* Main Content */
        .main-content {
            flex: 1;
            padding: 2rem;
            transition: margin-left 0.3s ease;
        }
        
        .main-content.expanded {
            margin-left: 0;
        }
        
        .page-header {
            margin-bottom: 2rem;
        }
        
        .page-header h1 {
            font-size: 1.75rem;
            font-weight: 700;
        }
        
        /* Dashboard Grid */
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border: 1px solid var(--border);
        }
        
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        
        .card-title {
            font-size: 1.125rem;
            font-weight: 600;
        }
        
        .stat-card {
            text-align: center;
        }
        
        .stat-value {
            font-size: 2.25rem;
            font-weight: 700;
            margin: 0.5rem 0;
        }
        
        .stat-label {
            color: var(--secondary);
            font-size: 0.875rem;
        }
        
        /* Patient List */
        .patient-list {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .patient-item {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 1rem;
            border-bottom: 1px solid var(--border);
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .patient-item:hover {
            background: #f8fafc;
        }
        
        .patient-avatar {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: var(--primary);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 1.125rem;
        }
        
        .patient-info h4 {
            font-weight: 600;
            margin-bottom: 0.25rem;
        }
        
        .patient-info p {
            color: var(--secondary);
            font-size: 0.875rem;
        }
        
        .patient-status {
            margin-left: auto;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        .status-waiting {
            background: #fef3c7;
            color: #d97706;
        }
        
        .status-in-progress {
            background: #dbeafe;
            color: var(--primary);
        }
        
        .status-completed {
            background: #dcfce7;
            color: #16a34a;
        }
        
        /* Live Monitoring */
        .monitoring-container {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 1.5rem;
        }
        
        .video-container {
            position: relative;
            background: black;
            border-radius: 12px;
            overflow: hidden;
        }
        
        #videoFeed {
            width: 100%;
            height: 400px;
            object-fit: cover;
        }
        
        .video-overlay {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(transparent, rgba(0,0,0,0.7));
            color: white;
            padding: 1rem;
        }
        
        .vitals-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
        }
        
        .vital-card {
            background: white;
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        }
        
        .vital-value {
            font-size: 1.5rem;
            font-weight: 700;
            margin: 0.5rem 0;
        }
        
        .vital-label {
            font-size: 0.875rem;
            color: var(--secondary);
        }
        
        /* Alerts */
        .alert {
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        
        .alert-warning {
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
        }
        
        .alert-danger {
            background: #fee2e2;
            border-left: 4px solid var(--danger);
        }
        
        .alert-success {
            background: #dcfce7;
            border-left: 4px solid var(--success);
        }
        
        /* Buttons */
        .btn {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .btn-primary {
            background: var(--primary);
            color: white;
        }
        
        .btn-primary:hover {
            background: var(--primary-dark);
        }
        
        .btn-outline {
            background: transparent;
            border: 1px solid var(--border);
            color: var(--dark);
        }
        
        .btn-outline:hover {
            background: #f8fafc;
        }
        
        /* Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            z-index: 1100;
            align-items: center;
            justify-content: center;
        }
        
        .modal-content {
            background: white;
            border-radius: 12px;
            width: 90%;
            max-width: 600px;
            max-height: 90vh;
            overflow-y: auto;
        }
        
        .modal-header {
            padding: 1.5rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .modal-body {
            padding: 1.5rem;
        }
        
        .close-modal {
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: var(--secondary);
        }
        
        /* Forms */
        .form-group {
            margin-bottom: 1rem;
        }
        
        .form-label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 600;
        }
        
        .form-control {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 1rem;
        }
        
        .form-control:focus {
            outline: none;
            border-color: var(--primary);
        }
        
        /* Responsive */
        @media (min-width: 1025px) {
            .main-content {
                margin-left: var(--sidebar-width);
            }
            
            .menu-toggle {
                display: none;
            }
        }
        
        @media (max-width: 1024px) {
            .monitoring-container {
                grid-template-columns: 1fr;
            }
            
            .sidebar {
                transform: translateX(-100%);
            }
            
            .sidebar.active {
                transform: translateX(0);
            }
            
            .main-content {
                margin-left: 0;
            }
        }
        
        @media (max-width: 768px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            
            .vitals-grid {
                grid-template-columns: 1fr 1fr;
            }
            
            .card-header {
                flex-direction: column;
                align-items: flex-start;
                gap: 1rem;
            }
            
            .card-header .btn {
                width: 100%;
                justify-content: center;
            }
            
            .top-navbar {
                padding: 0 1rem;
            }
            
            .main-content {
                padding: 1.5rem 1rem;
            }
        }
        
        @media (max-width: 480px) {
            .vitals-grid {
                grid-template-columns: 1fr;
            }
            
            .patient-item {
                flex-direction: column;
                text-align: center;
                gap: 0.5rem;
            }
            
            .patient-status {
                margin-left: 0;
            }
        }
    </style>
</head>
<body>
    <!-- Top Navbar -->
    <div class="top-navbar">
        <div class="nav-left">
            <button class="menu-toggle" id="menuToggle">☰</button>
            <div class="logo">
                <div class="logo-icon">MK</div>
                <div class="logo-text">MediKiosk Pro</div>
            </div>
        </div>
        
        <div class="nav-right">
            <div class="user-menu">
                <div class="user-avatar">DR</div>
                <span>Dr. Smith</span>
            </div>
        </div>
    </div>
    
    <!-- App Container -->
    <div class="app-container">
        <!-- Sidebar -->
        <div class="sidebar" id="sidebar">
            <div class="nav-section">
                <div class="nav-title">Main</div>
                <a href="#" class="nav-item active">
                    <i>📊</i> Dashboard
                </a>
                <a href="#" class="nav-item">
                    <i>👥</i> Patients
                </a>
                <a href="#" class="nav-item">
                    <i>📋</i> Appointments
                </a>
                <a href="#" class="nav-item">
                    <i>💊</i> Prescriptions
                </a>
            </div>
            
            <div class="nav-section">
                <div class="nav-title">Analysis</div>
                <a href="#" class="nav-item">
                    <i>❤️</i> Vital Signs
                </a>
                <a href="#" class="nav-item">
                    <i>🩺</i> Diagnostics
                </a>
                <a href="#" class="nav-item">
                    <i>📈</i> Health Trends
                </a>
            </div>
            
            <div class="nav-section">
                <div class="nav-title">Settings</div>
                <a href="#" class="nav-item">
                    <i>⚙️</i> System Settings
                </a>
                <a href="#" class="nav-item">
                    <i>👤</i> Profile
                </a>
                <a href="#" class="nav-item">
                    <i>🚪</i> Logout
                </a>
            </div>
        </div>
        
        <!-- Main Content -->
        <div class="main-content" id="mainContent">
            <div class="page-header">
                <h1>Patient Diagnosis Dashboard</h1>
            </div>
            
            <!-- Stats Overview -->
            <div class="dashboard-grid">
                <div class="card stat-card">
                    <div class="card-title">Today's Patients</div>
                    <div class="stat-value">12</div>
                    <div class="stat-label">Scheduled appointments</div>
                </div>
                
                <div class="card stat-card">
                    <div class="card-title">Waiting</div>
                    <div class="stat-value">3</div>
                    <div class="stat-label">Patients in queue</div>
                </div>
                
                <div class="card stat-card">
                    <div class="card-title">Avg. Heart Rate</div>
                    <div class="stat-value">72</div>
                    <div class="stat-label">BPM across patients</div>
                </div>
                
                <div class="card stat-card">
                    <div class="card-title">System Status</div>
                    <div class="stat-value" style="color: var(--success);">Online</div>
                    <div class="stat-label">All systems operational</div>
                </div>
            </div>
            
            <!-- Main Dashboard -->
            <div class="dashboard-grid" style="grid-template-columns: 2fr 1fr;">
                <!-- Live Monitoring Section -->
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">Live Patient Monitoring</div>
                        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                            <button class="btn btn-primary" onclick="startMonitoring()">
                                ▶ Start Diagnosis
                            </button>
                            <button class="btn btn-outline" onclick="stopMonitoring()">
                                ⏹ Stop
                            </button>
                        </div>
                    </div>
                    
                    <div class="monitoring-container">
                        <div class="video-container">
                            <img id="videoFeed" src="" alt="Live Camera Feed">
                            <div class="video-overlay">
                                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                                    <div>
                                        <div id="faceStatus" style="background: var(--danger); color: white; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.75rem;">
                                            No Face Detected
                                        </div>
                                    </div>
                                    <div style="display: flex; gap: 0.5rem;">
                                        <button class="btn btn-outline" style="background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3);">
                                            📸 Capture
                                        </button>
                                        <button class="btn btn-outline" style="background: rgba(255,255,255,0.2); color: white; border: 1px solid rgba(255,255,255,0.3);">
                                            📹 Record
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div>
                            <div class="card-title" style="margin-bottom: 1rem;">Vital Signs</div>
                            <div class="vitals-grid">
                                <div class="vital-card">
                                    <div class="vital-label">Heart Rate</div>
                                    <div class="vital-value" id="heartRate">--</div>
                                    <div class="vital-label">BPM</div>
                                </div>
                                
                                <div class="vital-card">
                                    <div class="vital-label">Stress Level</div>
                                    <div class="vital-value" id="stressLevel">--</div>
                                    <div class="vital-label">0-1 Scale</div>
                                </div>
                                
                                <div class="vital-card">
                                    <div class="vital-label">Fatigue Risk</div>
                                    <div class="vital-value" id="fatigueRisk">--</div>
                                    <div class="vital-label">Assessment</div>
                                </div>
                                
                                <div class="vital-card">
                                    <div class="vital-label">Confidence</div>
                                    <div class="vital-value" id="confidence">--</div>
                                    <div class="vital-label">Score</div>
                                </div>
                            </div>
                            
                            <div style="margin-top: 1rem;">
                                <div class="card-title">Health Status</div>
                                <div id="healthStatus" style="font-size: 1.25rem; font-weight: 600; color: var(--secondary); margin: 0.5rem 0;">
                                    No data
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Patient Queue -->
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">Patient Queue</div>
                        <button class="btn btn-outline" onclick="openNewPatientModal()">
                            + Add Patient
                        </button>
                    </div>
                    
                    <div class="patient-list">
                        <div class="patient-item">
                            <div class="patient-avatar">JS</div>
                            <div class="patient-info">
                                <h4>John Smith</h4>
                                <p>ID: P-12345 | 45 years</p>
                            </div>
                            <div class="patient-status status-in-progress">
                                In Progress
                            </div>
                        </div>
                        
                        <div class="patient-item">
                            <div class="patient-avatar">MJ</div>
                            <div class="patient-info">
                                <h4>Maria Johnson</h4>
                                <p>ID: P-12346 | 32 years</p>
                            </div>
                            <div class="patient-status status-waiting">
                                Waiting
                            </div>
                        </div>
                        
                        <div class="patient-item">
                            <div class="patient-avatar">RB</div>
                            <div class="patient-info">
                                <h4>Robert Brown</h4>
                                <p>ID: P-12347 | 58 years</p>
                            </div>
                            <div class="patient-status status-waiting">
                                Waiting
                            </div>
                        </div>
                        
                        <div class="patient-item">
                            <div class="patient-avatar">SW</div>
                            <div class="patient-info">
                                <h4>Sarah Wilson</h4>
                                <p>ID: P-12348 | 29 years</p>
                            </div>
                            <div class="patient-status status-completed">
                                Completed
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Alerts & Recommendations -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title">Alerts & Recommendations</div>
                </div>
                
                <div id="alertsContainer">
                    <div class="alert alert-warning">
                        <div>⚠️</div>
                        <div>System ready. Start monitoring to begin diagnosis.</div>
                    </div>
                </div>
                
                <div class="card-header" style="margin-top: 1.5rem;">
                    <div class="card-title">Diagnostic Notes</div>
                </div>
                
                <div class="form-group">
                    <textarea class="form-control" rows="4" placeholder="Enter diagnostic notes, observations, and recommendations..."></textarea>
                </div>
                
                <div style="display: flex; gap: 1rem; justify-content: flex-end; margin-top: 1rem; flex-wrap: wrap;">
                    <button class="btn btn-outline">Save Notes</button>
                    <button class="btn btn-primary">Generate Report</button>
                    <button class="btn btn-primary">Prescribe Medication</button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- New Patient Modal -->
    <div class="modal" id="newPatientModal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>Add New Patient</h3>
                <button class="close-modal" onclick="closeNewPatientModal()">×</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label class="form-label">Full Name</label>
                    <input type="text" class="form-control" placeholder="Enter patient name">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Date of Birth</label>
                    <input type="date" class="form-control">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Gender</label>
                    <select class="form-control">
                        <option>Male</option>
                        <option>Female</option>
                        <option>Other</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label class="form-label">Contact Information</label>
                    <input type="text" class="form-control" placeholder="Phone or email">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Medical History Notes</label>
                    <textarea class="form-control" rows="3" placeholder="Any relevant medical history..."></textarea>
                </div>
                
                <div style="display: flex; gap: 1rem; justify-content: flex-end; margin-top: 1.5rem; flex-wrap: wrap;">
                    <button class="btn btn-outline" onclick="closeNewPatientModal()">Cancel</button>
                    <button class="btn btn-primary">Add Patient</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        // WebSocket connection for live data
        let ws = null;
        let sessionId = null;
        
        // Responsive sidebar toggle
        const menuToggle = document.getElementById('menuToggle');
        const sidebar = document.getElementById('sidebar');
        const mainContent = document.getElementById('mainContent');
        
        menuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('active');
            mainContent.classList.toggle('expanded');
        });
        
        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function(event) {
            if (window.innerWidth <= 1024) {
                if (!sidebar.contains(event.target) && !menuToggle.contains(event.target)) {
                    sidebar.classList.remove('active');
                    mainContent.classList.remove('expanded');
                }
            }
        });
        
        // Adjust layout on window resize
        window.addEventListener('resize', function() {
            if (window.innerWidth > 1024) {
                sidebar.classList.remove('active');
                mainContent.classList.remove('expanded');
            }
        });
        
        async function startMonitoring() {
            try {
                const response = await fetch('/api/sessions/start', { method: 'POST' });
                const data = await response.json();
                sessionId = data.session_id;
                
                document.getElementById('alertsContainer').innerHTML = 
                    '<div class="alert alert-success">Starting diagnosis analysis...</div>';
                
                ws = new WebSocket(`ws://${window.location.host}/ws/${sessionId}`);
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    
                    // Update video feed
                    document.getElementById('videoFeed').src = 'data:image/jpeg;base64,' + data.frame;
                    
                    // Update face detection status
                    const faceStatus = document.getElementById('faceStatus');
                    if (data.face_detected) {
                        faceStatus.textContent = 'Face Detected';
                        faceStatus.style.background = 'var(--success)';
                    } else {
                        faceStatus.textContent = 'No Face Detected';
                        faceStatus.style.background = 'var(--danger)';
                    }
                    
                    // Update diagnosis data
                    if (data.diagnosis) {
                        document.getElementById('heartRate').textContent = data.diagnosis.heart_rate;
                        document.getElementById('stressLevel').textContent = data.diagnosis.stress_level;
                        document.getElementById('fatigueRisk').textContent = data.diagnosis.fatigue_risk;
                        document.getElementById('confidence').textContent = data.diagnosis.confidence;
                        
                        const healthStatus = document.getElementById('healthStatus');
                        healthStatus.textContent = data.diagnosis.health_status;
                        
                        if (data.diagnosis.health_status === 'Warning') {
                            healthStatus.style.color = 'var(--warning)';
                        } else if (data.diagnosis.health_status === 'Normal') {
                            healthStatus.style.color = 'var(--success)';
                        } else {
                            healthStatus.style.color = 'var(--secondary)';
                        }
                        
                        // Update alerts
                        const alertsContainer = document.getElementById('alertsContainer');
                        alertsContainer.innerHTML = '';
                        
                        data.diagnosis.alerts.forEach(alert => {
                            const alertElem = document.createElement('div');
                            alertElem.className = 'alert';
                            
                            if (alert.includes('Warning') || alert.includes('High') || alert.includes('Elevated')) {
                                alertElem.classList.add('alert-danger');
                            } else if (alert.includes('Normal')) {
                                alertElem.classList.add('alert-success');
                            } else {
                                alertElem.classList.add('alert-warning');
                            }
                            
                            alertElem.innerHTML = `
                                <div>${alert.includes('Warning') ? '⚠️' : 'ℹ️'}</div>
                                <div>${alert}</div>
                            `;
                            alertsContainer.appendChild(alertElem);
                        });
                    }
                };
                
                ws.onclose = function() {
                    document.getElementById('alertsContainer').innerHTML = 
                        '<div class="alert alert-warning">Diagnosis session ended.</div>';
                };
                
            } catch (error) {
                console.error('Error starting monitoring:', error);
                document.getElementById('alertsContainer').innerHTML = 
                    '<div class="alert alert-danger">Error starting monitoring session</div>';
            }
        }
        
        function stopMonitoring() {
            if (ws) {
                ws.close();
            }
            if (sessionId) {
                fetch(`/api/sessions/${sessionId}/stop`, { method: 'POST' });
                sessionId = null;
            }
        }
        
        // Modal functions
        function openNewPatientModal() {
            document.getElementById('newPatientModal').style.display = 'flex';
        }
        
        function closeNewPatientModal() {
            document.getElementById('newPatientModal').style.display = 'none';
        }
        
        // Close modal when clicking outside
        window.addEventListener('click', function(event) {
            const modal = document.getElementById('newPatientModal');
            if (event.target === modal) {
                closeNewPatientModal();
            }
        });
    </script>
</body>
</html>
    """