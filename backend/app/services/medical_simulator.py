# backend/app/services/medical_simulator.py
import random
import time
from datetime import datetime

class RealisticMedicalSim:
    def __init__(self):
        self.conditions_db = {
            "common_cold": {"symptoms": ["Cough", "Runny Nose", "Sore Throat"], "urgency": "low"},
            "flu": {"symptoms": ["Fever", "Body Aches", "Fatigue", "Cough"], "urgency": "medium"},
            "migraine": {"symptoms": ["Headache", "Nausea", "Light Sensitivity"], "urgency": "medium"},
            "hypertension": {"symptoms": ["Headache", "Dizziness"], "urgency": "high"},
            "asthma": {"symptoms": ["Wheezing", "Shortness of Breath"], "urgency": "high"}
        }
    
    def generate_realistic_vitals(self, age=30):
        """Generate medically plausible vital signs"""
        base_temp = 98.6
        temp_variation = random.uniform(-1, 3)  # Fever possibility
        
        return {
            "timestamp": datetime.now().isoformat(),
            "temperature": round(base_temp + temp_variation, 1),
            "heart_rate": random.randint(60, 100),
            "blood_pressure": {
                "systolic": random.randint(110, 160),
                "diastolic": random.randint(70, 100)
            },
            "respiratory_rate": random.randint(12, 20),
            "oxygen_saturation": random.randint(95, 99)
        }
    
    def analyze_symptoms(self, symptoms, vitals):
        """Real symptom analysis using your RTX for processing"""
        matched_conditions = []
        
        for condition, data in self.conditions_db.items():
            symptom_matches = set(symptoms) & set(data["symptoms"])
            if symptom_matches:
                match_score = len(symptom_matches) / len(data["symptoms"])
                if match_score > 0.3:  # 30% match threshold
                    matched_conditions.append({
                        "condition": condition,
                        "matched_symptoms": list(symptom_matches),
                        "confidence": round(match_score * 100),
                        "urgency": data["urgency"]
                    })
        
        # Sort by confidence
        return sorted(matched_conditions, key=lambda x: x["confidence"], reverse=True)