import numpy as np
from collections import deque
import time
from typing import Dict, List
import asyncio
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
import logging
import hashlib
import re
import os

logger = logging.getLogger(__name__)

class RealTimeMedicalDiagnosis:
    def __init__(self):
        self.bpm_history = deque(maxlen=15)
        self.stress_history = deque(maxlen=15)
        self.last_update_time = time.time()
        self.last_ai_advice = "AI medical assessment will appear here..."
        self.ai_processing = False
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.recommendation_history = deque(maxlen=20)
        self.last_vital_hash = None
        self.ai_call_counter = 0
        self.last_ai_call_time = 0
        
        # Set GPU environment variables
        self._setup_gpu_environment()
        
    def _setup_gpu_environment(self):
        """Setup environment for GPU acceleration"""
        # Force GPU usage for Ollama
        os.environ['OLLAMA_GPU_LAYERS'] = '50'
        os.environ['OLLAMA_NUM_GPU'] = '1'
        
        # For NVIDIA GPUs
        os.environ['CUDA_VISIBLE_DEVICES'] = '0'
        
    async def get_ai_medical_advice_async(self, vital_signs: Dict) -> str:
        """Get AI medical advice using GPU acceleration"""
        current_time = time.time()
        
        # Only call AI every 10 seconds to avoid spamming
        if current_time - self.last_ai_call_time < 10 and self.last_ai_advice != "AI medical assessment will appear here...":
            return self.last_ai_advice
            
        if self.ai_processing:
            return self.last_ai_advice
            
        # Check if vital signs have changed significantly
        current_hash = self._get_vital_signs_hash(vital_signs)
        if current_hash == self.last_vital_hash and self.last_ai_advice != "AI medical assessment will appear here...":
            return self.last_ai_advice
            
        self.last_vital_hash = current_hash
        self.ai_processing = True
        self.last_ai_call_time = current_time
        
        try:
            # Create a prompt that encourages varied responses
            prompt = f"""
            Patient presents with the following real-time vital signs:
            - Heart Rate: {vital_signs['heart_rate']} BPM
            - Stress Level: {vital_signs['stress_level']}/1.0
            - Fatigue Risk: {vital_signs['fatigue_risk']}
            - Health Status: {vital_signs['health_status']}
            - Recent Alerts: {', '.join(vital_signs['alerts'])}
            
            Provide a brief medical assessment and 1-2 specific, actionable recommendations. 
            Focus on immediate, practical advice. Be concise (2-3 sentences max).
            Avoid repeating previous recommendations if possible.
            """
            
            # Run Ollama in a separate thread with GPU acceleration
            loop = asyncio.get_event_loop()
            advice = await loop.run_in_executor(
                self.executor, 
                self._call_ollama_with_gpu, 
                prompt
            )
        
            self.last_ai_advice = advice
            return advice
            
        except Exception as e:
            logger.error(f"AI model error: {e}")
            return "AI medical assessment temporarily unavailable. Please try again."
        finally:
            self.ai_processing = False
    
    def _call_ollama_with_gpu(self, prompt: str) -> str:
        """Call Ollama with GPU acceleration"""
        try:
            # Test if Ollama is running and the model is available
            test_result = subprocess.run([
                'ollama', 'list'
            ], capture_output=True, text=True, timeout=10)
            
            if test_result.returncode != 0:
                return "AI service is not available. Please ensure Ollama is running."
            
            # Check if the model exists
            if 'gooddoctor' not in test_result.stdout:
                return "Medical AI model not found. Please pull the model first."
            
            # Run with GPU acceleration
            result = subprocess.run([
                'ollama', 'run', 
                '--gpu',  # Force GPU usage
                'ALIENTELLIGENCE/gooddoctor:latest', 
                prompt
            ], 
            capture_output=True, 
            text=True, 
            timeout=25,  # Reduced timeout since GPU should be faster
            encoding='utf-8',
            errors='ignore',
            env=os.environ  # Pass the GPU environment variables
            )

            if result.returncode == 0 and result.stdout.strip():
                response = result.stdout.strip()
                # Clean up the response
                if ">>>" in response:
                    response = response.split(">>>")[-1].strip()
                if response.startswith('"') and response.endswith('"'):
                    response = response[1:-1]
                
                return response if response else "AI is processing your health data..."
            else:
                # If GPU fails, try CPU as fallback
                return self._call_ollama_cpu_fallback(prompt)
                
        except subprocess.TimeoutExpired:
            logger.warning("Ollama GPU call timed out, falling back to CPU")
            return self._call_ollama_cpu_fallback(prompt)
        except Exception as e:
            logger.error(f"Ollama GPU call failed: {e}, falling back to CPU")
            return self._call_ollama_cpu_fallback(prompt)
    
    def _call_ollama_cpu_fallback(self, prompt: str) -> str:
        """Fallback to CPU if GPU fails"""
        try:
            result = subprocess.run([
                'ollama', 'run', 
                'ALIENTELLIGENCE/gooddoctor:latest', 
                prompt
            ], 
            capture_output=True, 
            text=True, 
            timeout=30,
            encoding='utf-8',
            errors='ignore'
            )

            if result.returncode == 0 and result.stdout.strip():
                response = result.stdout.strip()
                if ">>>" in response:
                    response = response.split(">>>")[-1].strip()
                if response.startswith('"') and response.endswith('"'):
                    response = response[1:-1]
                
                return response if response else "AI is processing your health data..."
            else:
                error_msg = result.stderr if result.stderr else "Unknown error"
                return f"AI service error: {error_msg}"
                
        except subprocess.TimeoutExpired:
            return "AI analysis taking longer than expected. Please wait..."
        except Exception as e:
            return f"AI service unavailable: {str(e)}"
    
    def _get_vital_signs_hash(self, vital_signs: Dict) -> str:
        """Create a hash of vital signs to detect significant changes"""
        key_data = f"{vital_signs['heart_rate']:.1f}-{vital_signs['stress_level']:.2f}-{vital_signs['health_status']}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    # ... rest of your existing methods remain the same ...
    def extract_recommendations_from_advice(self, advice: str) -> List[Dict]:
        """Extract structured recommendations from AI advice"""
        if not advice or any(phrase in advice.lower() for phrase in ['analyzing', 'unavailable', 'error', 'processing']):
            return []
            
        recommendations = []
        
        # More sophisticated pattern matching
        patterns = [
            (r'(?:recommend|suggest|advise|encourage)\s+(.*?)(?=\.|$)', 'general'),
            (r'(?:should|could|might)\s+(.*?)(?=\.|$)', 'suggestion'),
            (r'(?:consider|try)\s+(.*?)(?=\.|$)', 'consideration'),
        ]
        
        for pattern, rec_type in patterns:
            matches = re.finditer(pattern, advice, re.IGNORECASE)
            for match in matches:
                rec_text = match.group(1).strip()
                if len(rec_text) > 15:  # Minimum meaningful length
                    category = self._categorize_recommendation(rec_text)
                    rec_id = hashlib.md5(rec_text.encode()).hexdigest()[:8]
                    
                    recommendation = {
                        'id': rec_id,
                        'text': rec_text,
                        'category': category,
                        'type': rec_type,
                        'timestamp': time.time(),
                        'full_advice': advice
                    }
                    recommendations.append(recommendation)
        
        # If no structured recommendations found, use key sentences
        if not recommendations and len(advice) > 50:
            sentences = [s.strip() for s in re.split(r'[.!?]+', advice) if len(s.strip()) > 30]
            for sentence in sentences[:2]:  # Take max 2 sentences
                category = self._categorize_recommendation(sentence)
                rec_id = hashlib.md5(sentence.encode()).hexdigest()[:8]
                
                recommendation = {
                    'id': rec_id,
                    'text': sentence,
                    'category': category,
                    'type': 'general',
                    'timestamp': time.time(),
                    'full_advice': advice
                }
                recommendations.append(recommendation)
        
        return recommendations
    
    def _categorize_recommendation(self, text: str) -> str:
        """Categorize recommendation based on content"""
        text_lower = text.lower()
        
        categories = {
            'Relaxation': ['breath', 'breathe', 'relax', 'meditate', 'calm', 'mindful'],
            'Exercise': ['exercise', 'activity', 'walk', 'movement', 'physical', 'yoga'],
            'Stress Management': ['stress', 'anxiety', 'pressure', 'cope', 'manage stress'],
            'Sleep & Rest': ['sleep', 'rest', 'fatigue', 'tired', 'energy', 'nap'],
            'Nutrition': ['diet', 'food', 'water', 'hydrate', 'eat', 'nutrition', 'meal'],
            'Monitoring': ['monitor', 'check', 'track', 'measure', 'observe', 'watch'],
            'Lifestyle': ['routine', 'habit', 'lifestyle', 'daily', 'regular'],
            'Medical': ['doctor', 'medical', 'professional', 'clinic', 'hospital']
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return 'General Health'
    
    def analyze_vitals(self, bpm: float, confidence: float) -> Dict:
        if bpm == 0 or confidence < 0.2:
            return {
                'heart_rate': 0,
                'stress_level': 0,
                'fatigue_risk': 'Unknown',
                'health_status': 'No data',
                'alerts': ['Detecting face...'],
                'confidence': 0,
                'ai_advice': 'Please position yourself clearly in front of the camera for analysis.',
                'recommendations': []
            }
        
        self.bpm_history.append(bpm)
        stress_level = 1.0 - min(confidence, 1.0)
        self.stress_history.append(stress_level)
        
        alerts = []
        health_status = "Normal"
        fatigue_risk = "Low"
        
        # Heart rate analysis
        if bpm > 100:
            alerts.append("Elevated heart rate")
            health_status = "Warning"
        elif bpm < 50:
            alerts.append("Low heart rate")
            health_status = "Warning"
        else:
            alerts.append("Normal heart rate")
        
        # Stress analysis
        avg_stress = np.mean(list(self.stress_history)) if self.stress_history else 0
        if avg_stress > 0.7:
            alerts.append("High stress detected")
            fatigue_risk = "High"
        elif avg_stress > 0.5:
            alerts.append("Moderate stress")
            fatigue_risk = "Medium"
        else:
            alerts.append("Low stress")
        
        # Fatigue detection
        if len(self.bpm_history) >= 8:
            recent_avg = np.mean(list(self.bpm_history)[-4:])
            earlier_avg = np.mean(list(self.bpm_history)[-8:-4])
            if earlier_avg - recent_avg > 8:
                alerts.append("Possible fatigue detected")
                fatigue_risk = "High"
        
        vital_signs = {
            'heart_rate': round(bpm, 1),
            'stress_level': round(avg_stress, 2),
            'fatigue_risk': fatigue_risk,
            'health_status': health_status,
            'alerts': alerts,
            'confidence': round(confidence, 2),
            'update_count': len(self.bpm_history),
            'ai_advice': self.last_ai_advice,
            'recommendations': self._get_current_recommendations()
        }
        
        return vital_signs
    
    def _get_current_recommendations(self) -> List[Dict]:
        """Get current recommendations without duplicates"""
        unique_recs = {}
        for rec in self.recommendation_history:
            unique_recs[rec['id']] = rec
        
        return list(unique_recs.values())[-15:]  
    
    def update_ai_advice(self, new_advice: str):
        """Update AI advice and extract recommendations"""
        if new_advice and new_advice != self.last_ai_advice:
            self.last_ai_advice = new_advice
            
            # Extract and store new recommendations
            new_recommendations = self.extract_recommendations_from_advice(new_advice)
            for rec in new_recommendations:
                # Check for duplicates before adding
                if not any(existing_rec['id'] == rec['id'] for existing_rec in self.recommendation_history):
                    self.recommendation_history.append(rec)