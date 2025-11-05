import numpy as np
from collections import deque
from typing import List, Dict

class PostProcessor:
    def __init__(self, window_size: int = 10):
        self.bpm_buffer = deque(maxlen=window_size)
        self.stress_buffer = deque(maxlen=window_size)
        self.confidence_buffer = deque(maxlen=window_size)
        
    def add_measurement(self, bpm: float, stress: float, confidence: float):
        """Add new measurement to buffers"""
        if confidence > 0.3:  # Only use confident measurements
            self.bpm_buffer.append(bpm)
            self.stress_buffer.append(stress)
        self.confidence_buffer.append(confidence)
    
    def get_smoothed_metrics(self) -> Dict:
        """Get smoothed metrics using moving average"""
        if not self.bpm_buffer:
            return {'bpm': 0, 'stress': 0, 'confidence': 0}
        
        avg_bpm = np.mean(list(self.bpm_buffer))
        avg_stress = np.mean(list(self.stress_buffer))
        avg_confidence = np.mean(list(self.confidence_buffer))
        
        return {
            'bpm': avg_bpm,
            'stress': avg_stress,
            'confidence': avg_confidence
        }
    
    def detect_fatigue_trend(self, bpm_history: List[float]) -> bool:
        """Detect fatigue based on heart rate trends"""
        if len(bpm_history) < 10:
            return False
        
        recent = np.mean(bpm_history[-5:])
        earlier = np.mean(bpm_history[-10:-5])
        
        # Fatigue indicator: significant drop in heart rate
        return (earlier - recent) > 10  # BPM drop
    
    def detect_stress_trend(self, stress_history: List[float]) -> bool:
        """Detect stress based on stress index trends"""
        if len(stress_history) < 5:
            return False
        
        recent_stress = np.mean(stress_history[-3:])
        return recent_stress > 0.7  # High stress threshold

class AlertSystem:
    def __init__(self):
        self.alerts = []
        
    def check_alerts(self, metrics: Dict) -> List[str]:
        """Check for alert conditions"""
        alerts = []
        
        # Heart rate alerts
        if metrics['bpm'] > 100:
            alerts.append("Elevated Heart Rate")
        elif metrics['bpm'] < 50:
            alerts.append("Low Heart Rate")
            
        # Stress alerts
        if metrics['stress'] > 0.8:
            alerts.append("High Stress Level")
        elif metrics['stress'] > 0.6:
            alerts.append("Moderate Stress")
            
        return alerts