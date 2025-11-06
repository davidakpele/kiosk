import numpy as np
from collections import deque
from scipy import signal
from scipy.fft import fft, fftfreq
import cv2

class FastRPPGProcessor:
    def __init__(self, fps=30, window_size=120):
        self.fps = fps
        self.window_size = window_size
        self.signal_buffer = deque(maxlen=window_size)
        self.b, self.a = signal.butter(2, [0.8, 3.0], btype='bandpass', fs=fps)
        
    def extract_signal(self, frame, landmarks) -> float:
        if not landmarks:
            return 0
            
        h, w = frame.shape[:2]
        landmarks_array = np.array([(lm.x * w, lm.y * h) for lm in landmarks.landmark])
        
        forehead_indices = [10, 67, 108, 151, 337, 332]
        forehead_pts = landmarks_array[forehead_indices].astype(np.int32)
        
        x, y, w_roi, h_roi = cv2.boundingRect(forehead_pts)
        if (w_roi > 0 and h_roi > 0 and 
            x + w_roi < frame.shape[1] and 
            y + h_roi < frame.shape[0]):
            roi = frame[y:y+h_roi, x:x+w_roi]
            if roi.size > 0:
                return np.mean(roi[:, :, 1])
        
        return 0
    
    def add_signal(self, signal_value: float):
        self.signal_buffer.append(signal_value)
    
    def compute_heart_rate(self) -> tuple[float, float]:
        if len(self.signal_buffer) < 40:
            return 0, 0
        
        signal_array = np.array(self.signal_buffer)
        
        try:
            signal_detrended = signal.detrend(signal_array)
            signal_filtered = signal.filtfilt(self.b, self.a, signal_detrended)
            
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

        except Exception:
            return 0, 0