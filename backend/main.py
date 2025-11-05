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

app = FastAPI(
    title="AI Medical Kiosk - LIVE CAMERA",
    version="3.0.0",
    description="Real-time medical kiosk with live camera processing"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

monitoring_sessions: Dict[str, Dict] = {}

class FaceProcessor:
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

class RPPGProcessor:
    def __init__(self, fps=30, window_size=150):
        self.fps = fps
        self.window_size = window_size
        self.signal_buffer = deque(maxlen=window_size)
        self.b, self.a = signal.butter(3, [0.8, 3.0], btype='bandpass', fs=fps)
    
    def extract_signal(self, frame, landmarks):
        if not landmarks:
            return 0
            
        h, w = frame.shape[:2]
        landmarks_array = np.array([(lm.x * w, lm.y * h) for lm in landmarks.landmark])
        
        # Use forehead region for rPPG
        forehead_indices = [10, 67, 69, 104, 108, 151, 337, 338, 297, 332]
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
        if len(self.signal_buffer) < 50:
            return 0, 0
        
        signal_array = np.array(self.signal_buffer)
        signal_detrended = signal.detrend(signal_array)
        
        try:
            signal_filtered = signal.filtfilt(self.b, self.a, signal_detrended)
        except:
            signal_filtered = signal_detrended
        
        # FFT analysis
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

class MedicalDiagnosis:
    def __init__(self):
        self.bpm_history = deque(maxlen=10)
        self.stress_history = deque(maxlen=10)
    
    def analyze_vitals(self, bpm, confidence):
        if bpm == 0 or confidence < 0.3:
            return {
                'heart_rate': 0,
                'stress_level': 0,
                'fatigue_risk': 'Unknown',
                'health_status': 'No data',
                'alerts': ['No face detected or low confidence']
            }
        
        self.bpm_history.append(bpm)
        stress_level = 1.0 - min(confidence, 1.0)
        self.stress_history.append(stress_level)
        
        # Medical analysis
        alerts = []
        health_status = "Normal"
        fatigue_risk = "Low"
        
        # Heart rate analysis
        if bpm > 100:
            alerts.append("Elevated heart rate detected")
            health_status = "Warning"
        elif bpm < 50:
            alerts.append("Low heart rate detected")
            health_status = "Warning"
        
        # Stress analysis
        avg_stress = np.mean(list(self.stress_history)) if self.stress_history else 0
        if avg_stress > 0.7:
            alerts.append("High stress level detected")
            fatigue_risk = "High"
        elif avg_stress > 0.5:
            alerts.append("Moderate stress level detected")
            fatigue_risk = "Medium"
        
        # Fatigue detection
        if len(self.bpm_history) >= 5:
            recent_avg = np.mean(list(self.bpm_history)[-3:])
            earlier_avg = np.mean(list(self.bpm_history)[-5:-2])
            if earlier_avg - recent_avg > 10:
                alerts.append("Possible fatigue detected")
                fatigue_risk = "High"
        
        if not alerts:
            alerts.append("All vitals normal")
        
        return {
            'heart_rate': round(bpm, 1),
            'stress_level': round(avg_stress, 2),
            'fatigue_risk': fatigue_risk,
            'health_status': health_status,
            'alerts': alerts,
            'confidence': round(confidence, 2)
        }

class Camera:
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

class MonitoringSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.camera = Camera()
        self.face_processor = FaceProcessor()
        self.rppg_processor = RPPGProcessor()
        self.diagnosis = MedicalDiagnosis()
        self.is_running = False
        self.frame_count = 0
        
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
        
        # Process face detection
        face_results = self.face_processor.process_frame(frame)
        
        diagnosis_result = None
        if face_results['face_detected']:
            # Extract rPPG signal every 3 frames
            if self.frame_count % 3 == 0:
                signal_value = self.rppg_processor.extract_signal(frame, face_results['landmarks'])
                self.rppg_processor.add_signal(signal_value)
                
                # Compute heart rate every 30 frames (1 second)
                if self.frame_count % 30 == 0 and len(self.rppg_processor.signal_buffer) >= 50:
                    bpm, confidence = self.rppg_processor.compute_heart_rate()
                    diagnosis_result = self.diagnosis.analyze_vitals(bpm, confidence)
        
        self.frame_count += 1
        
        # Draw face landmarks if detected
        if face_results['face_detected'] and face_results['landmarks']:
            frame = self.draw_landmarks(frame, face_results['landmarks'])
        
        # Add diagnosis overlay
        if diagnosis_result:
            frame = self.add_diagnosis_overlay(frame, diagnosis_result)
        
        _, buffer = cv2.imencode('.jpg', cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return {
            'frame': frame_base64,
            'timestamp': datetime.now().isoformat(),
            'diagnosis': diagnosis_result,
            'face_detected': face_results['face_detected']
        }
    
    def draw_landmarks(self, frame, landmarks):
        h, w = frame.shape[:2]
        for landmark in landmarks.landmark:
            x, y = int(landmark.x * w), int(landmark.y * h)
            cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)
        return frame
    
    def add_diagnosis_overlay(self, frame, diagnosis):
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (400, 180), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)
        
        texts = [
            f"HR: {diagnosis['heart_rate']} BPM",
            f"Stress: {diagnosis['stress_level']}",
            f"Fatigue: {diagnosis['fatigue_risk']}",
            f"Status: {diagnosis['health_status']}",
            f"Conf: {diagnosis['confidence']}"
        ]
        
        for i, text in enumerate(texts):
            color = (0, 255, 0)  # Green
            if 'Warning' in text:
                color = (0, 165, 255)  # Orange
            elif 'High' in text:
                color = (0, 0, 255)  # Red
                
            cv2.putText(frame, text, (20, 40 + i * 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        return frame

@app.get("/")
async def root():
    return {"message": "Medical Kiosk API", "status": "running"}

@app.post("/api/sessions/start")
async def start_monitoring_session():
    session_id = str(uuid.uuid4())
    monitoring_session = MonitoringSession(session_id)
    monitoring_session.start()
    monitoring_sessions[session_id] = monitoring_session
    return {"session_id": session_id, "message": "Monitoring session started"}

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
            result = monitoring_session.process_frame()
            if result:
                await websocket.send_json(result)
            await asyncio.sleep(0.033)
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        print(f"Error in WebSocket: {e}")
    finally:
        await websocket.close()

@app.get("/monitor", response_class=HTMLResponse)
async def get_monitor_page():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Medical Kiosk - LIVE DIAGNOSIS</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { display: flex; gap: 20px; max-width: 1400px; margin: 0 auto; }
            .video-panel { flex: 2; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .metrics-panel { flex: 1; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            #videoFeed { width: 100%; border: 2px solid #e0e0e0; border-radius: 5px; }
            .metric-card { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }
            .metric-value { font-size: 24px; font-weight: bold; color: #333; }
            .metric-label { font-size: 14px; color: #666; }
            .alert { background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 5px 0; border-radius: 3px; }
            .warning { background: #f8d7da; border-left: 4px solid #dc3545; }
            .success { background: #d1edff; border-left: 4px solid #007bff; }
            button { padding: 12px 24px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
            .btn-start { background: #28a745; color: white; }
            .btn-stop { background: #dc3545; color: white; }
            .status-indicator { padding: 8px 15px; border-radius: 20px; color: white; font-weight: bold; }
            .status-green { background: #28a745; }
            .status-red { background: #dc3545; }
            .status-orange { background: #fd7e14; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="video-panel">
                <h1>🩺 AI Medical Kiosk - Live Diagnosis</h1>
                <div style="margin-bottom: 20px;">
                    <button class="btn-start" onclick="startMonitoring()">▶ Start Diagnosis</button>
                    <button class="btn-stop" onclick="stopMonitoring()">⏹ Stop Diagnosis</button>
                    <span id="faceStatus" class="status-indicator status-red">No Face Detected</span>
                </div>
                <img id="videoFeed" src="" alt="Live Camera Feed">
            </div>
            <div class="metrics-panel">
                <h3>📊 Real-time Diagnosis</h3>
                <div id="diagnostics">
                    <div class="metric-card">
                        <div class="metric-label">Heart Rate</div>
                        <div class="metric-value" id="heartRate">-- BPM</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Stress Level</div>
                        <div class="metric-value" id="stressLevel">--</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Fatigue Risk</div>
                        <div class="metric-value" id="fatigueRisk">--</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Health Status</div>
                        <div class="metric-value" id="healthStatus">--</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Confidence</div>
                        <div class="metric-value" id="confidence">--</div>
                    </div>
                </div>
                
                <h3>⚠️ Alerts & Recommendations</h3>
                <div id="alertsContainer">
                    <div class="alert">System ready. Start monitoring to begin diagnosis.</div>
                </div>
            </div>
        </div>

        <script>
            let ws = null;
            let sessionId = null;
            
            async function startMonitoring() {
                const response = await fetch('/api/sessions/start', { method: 'POST' });
                const data = await response.json();
                sessionId = data.session_id;
                
                document.getElementById('alertsContainer').innerHTML = '<div class="alert">Starting diagnosis analysis...</div>';
                
                ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    
                    // Update video feed
                    document.getElementById('videoFeed').src = 'data:image/jpeg;base64,' + data.frame;
                    
                    // Update face detection status
                    const faceStatus = document.getElementById('faceStatus');
                    if (data.face_detected) {
                        faceStatus.textContent = 'Face Detected';
                        faceStatus.className = 'status-indicator status-green';
                    } else {
                        faceStatus.textContent = 'No Face Detected';
                        faceStatus.className = 'status-indicator status-red';
                    }
                    
                    // Update diagnosis data
                    if (data.diagnosis) {
                        document.getElementById('heartRate').textContent = data.diagnosis.heart_rate + ' BPM';
                        document.getElementById('stressLevel').textContent = data.diagnosis.stress_level;
                        document.getElementById('fatigueRisk').textContent = data.diagnosis.fatigue_risk;
                        document.getElementById('healthStatus').textContent = data.diagnosis.health_status;
                        document.getElementById('confidence').textContent = data.diagnosis.confidence;
                        
                        // Update alerts
                        const alertsContainer = document.getElementById('alertsContainer');
                        alertsContainer.innerHTML = '';
                        
                        data.diagnosis.alerts.forEach(alert => {
                            const alertElem = document.createElement('div');
                            alertElem.className = 'alert';
                            
                            if (alert.includes('Warning') || alert.includes('High') || alert.includes('Elevated')) {
                                alertElem.className += ' warning';
                            } else if (alert.includes('Normal')) {
                                alertElem.className += ' success';
                            }
                            
                            alertElem.textContent = alert;
                            alertsContainer.appendChild(alertElem);
                        });
                    }
                };
                
                ws.onclose = function() {
                    document.getElementById('alertsContainer').innerHTML = '<div class="alert">Diagnosis session ended.</div>';
                };
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
        </script>
    </body>
    </html>
    """