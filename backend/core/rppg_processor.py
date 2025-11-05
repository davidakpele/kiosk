import numpy as np
from scipy import signal
from scipy.fft import fft, fftfreq
import cv2
from typing import Dict, List

class RPPGProcessor:
    def __init__(self, fps: int = 30, window_size: int = 150):
        self.fps = fps
        self.window_size = window_size
        self.signal_buffer = []
        self.timestamps = []
        
        # Bandpass filter for heart rate (0.8 Hz to 3.0 Hz ≈ 48-180 BPM)
        self.b, self.a = signal.butter(3, [0.8, 3.0], btype='bandpass', fs=fps)
    
    def process_roi(self, roi: np.ndarray) -> float:
        """Extract rPPG signal from ROI"""
        if roi.size == 0:
            return 0.0
            
        # Use green channel (most sensitive to blood volume changes)
        if len(roi.shape) == 3:
            green_channel = roi[:, :, 1]
            signal_value = np.mean(green_channel)
        else:
            signal_value = np.mean(roi)
            
        return float(signal_value)
    
    def add_signal_point(self, signal_value: float, timestamp: float):
        """Add signal point to buffer"""
        self.signal_buffer.append(signal_value)
        self.timestamps.append(timestamp)
        
        # Maintain window size
        if len(self.signal_buffer) > self.window_size:
            self.signal_buffer.pop(0)
            self.timestamps.pop(0)
    
    def compute_heart_rate(self) -> Dict:
        """Compute heart rate from rPPG signal"""
        if len(self.signal_buffer) < self.window_size:
            return {'bpm': 0, 'confidence': 0, 'spectrum': None}
        
        signal_array = np.array(self.signal_buffer)
        
        # Detrend signal
        signal_detrended = signal.detrend(signal_array)
        
        # Apply bandpass filter
        try:
            signal_filtered = signal.filtfilt(self.b, self.a, signal_detrended)
        except:
            signal_filtered = signal_detrended
        
        # Apply Hann window
        window = signal.windows.hann(len(signal_filtered))
        signal_windowed = signal_filtered * window
        
        # FFT analysis
        fft_result = fft(signal_windowed)
        frequencies = fftfreq(len(signal_windowed), 1.0 / self.fps)
        
        # Get magnitude in positive frequencies
        positive_freq_idx = frequencies > 0
        positive_freq = frequencies[positive_freq_idx]
        magnitude = np.abs(fft_result[positive_freq_idx])
        
        # Find peak in heart rate range (0.8-3.0 Hz)
        hr_mask = (positive_freq >= 0.8) & (positive_freq <= 3.0)
        if not np.any(hr_mask):
            return {'bpm': 0, 'confidence': 0, 'spectrum': (positive_freq, magnitude)}
        
        hr_freq = positive_freq[hr_mask]
        hr_magnitude = magnitude[hr_mask]
        
        if len(hr_magnitude) == 0:
            return {'bpm': 0, 'confidence': 0, 'spectrum': (positive_freq, magnitude)}
        
        peak_idx = np.argmax(hr_magnitude)
        dominant_freq = hr_freq[peak_idx]
        
        # Convert to BPM
        bpm = dominant_freq * 60.0
        
        # Simple confidence based on peak prominence
        confidence = min(hr_magnitude[peak_idx] / np.mean(magnitude), 1.0)
        
        return {
            'bpm': bpm,
            'confidence': confidence,
            'spectrum': (positive_freq, magnitude)
        }
    
    def compute_stress_index(self, hr_variability: float) -> float:
        """Compute stress index based on heart rate variability"""
        # Simple stress index: lower HRV = higher stress
        # Normalize based on typical HRV ranges
        base_hrv = 50  # ms
        stress_index = max(0, min(1, 1 - (hr_variability / base_hrv)))
        return stress_index
    
    def clear_buffer(self):
        """Clear signal buffer"""
        self.signal_buffer.clear()
        self.timestamps.clear()