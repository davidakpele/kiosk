#!/usr/bin/env python3
"""
Add medical knowledge base - Symptoms, Conditions, and Mappings
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import SessionLocal
from app.models.symptom import Symptom, Condition, SymptomConditionMapping

def add_medical_knowledge():
    db = SessionLocal()
    
    # Clear existing data
    db.query(SymptomConditionMapping).delete()
    db.query(Symptom).delete()
    db.query(Condition).delete()
    
    # Add Symptoms
    symptoms_data = [
        # Cardiac Symptoms
        {"name": "Chest Pain", "category": "cardiac", "severity_level": "high", "body_part": "chest", "is_emergency": True},
        {"name": "Shortness of Breath", "category": "cardiac", "severity_level": "high", "body_part": "chest", "is_emergency": True},
        {"name": "Heart Palpitations", "category": "cardiac", "severity_level": "medium", "body_part": "chest", "is_emergency": False},
        {"name": "Swollen Ankles", "category": "cardiac", "severity_level": "medium", "body_part": "legs", "is_emergency": False},
        
        # Neurological Symptoms
        {"name": "Headache", "category": "neurological", "severity_level": "low", "body_part": "head", "is_emergency": False},
        {"name": "Dizziness", "category": "neurological", "severity_level": "medium", "body_part": "head", "is_emergency": False},
        {"name": "Numbness", "category": "neurological", "severity_level": "high", "body_part": "limbs", "is_emergency": True},
        {"name": "Vision Problems", "category": "neurological", "severity_level": "medium", "body_part": "head", "is_emergency": False},
        
        # Respiratory Symptoms
        {"name": "Cough", "category": "respiratory", "severity_level": "low", "body_part": "chest", "is_emergency": False},
        {"name": "Wheezing", "category": "respiratory", "severity_level": "medium", "body_part": "chest", "is_emergency": False},
        {"name": "Chest Tightness", "category": "respiratory", "severity_level": "high", "body_part": "chest", "is_emergency": True},
        
        # General Symptoms
        {"name": "Fever", "category": "general", "severity_level": "medium", "body_part": "whole_body", "is_emergency": False},
        {"name": "Fatigue", "category": "general", "severity_level": "low", "body_part": "whole_body", "is_emergency": False},
        {"name": "Nausea", "category": "general", "severity_level": "medium", "body_part": "abdomen", "is_emergency": False},
    ]
    
    symptoms = []
    for data in symptoms_data:
        symptom = Symptom(**data)
        db.add(symptom)
        symptoms.append(symptom)
    
    db.commit()
    print(f"✅ Added {len(symptoms)} symptoms")
    
    # Add Conditions
    conditions_data = [
        {"name": "Heart Attack", "specialty": "Cardiology", "urgency_level": "emergency"},
        {"name": "Heart Failure", "specialty": "Cardiology", "urgency_level": "high"},
        {"name": "Hypertension", "specialty": "Cardiology", "urgency_level": "medium"},
        
        {"name": "Stroke", "specialty": "Neurology", "urgency_level": "emergency"},
        {"name": "Migraine", "specialty": "Neurology", "urgency_level": "medium"},
        {"name": "Epilepsy", "specialty": "Neurology", "urgency_level": "high"},
        
        {"name": "Asthma", "specialty": "Pulmonology", "urgency_level": "high"},
        {"name": "Pneumonia", "specialty": "Pulmonology", "urgency_level": "high"},
        {"name": "COPD", "specialty": "Pulmonology", "urgency_level": "medium"},
        
        {"name": "Common Cold", "specialty": "General Medicine", "urgency_level": "low"},
        {"name": "Flu", "specialty": "General Medicine", "urgency_level": "medium"},
        {"name": "Viral Infection", "specialty": "General Medicine", "urgency_level": "low"},
    ]
    
    conditions = []
    for data in conditions_data:
        condition = Condition(**data)
        db.add(condition)
        conditions.append(condition)
    
    db.commit()
    print(f"✅ Added {len(conditions)} conditions")
    
    # Create Symptom-Condition Mappings (Medical Knowledge Base)
    mappings = [
        # Heart Attack mappings
        {"symptom_name": "Chest Pain", "condition_name": "Heart Attack", "confidence": 90},
        {"symptom_name": "Shortness of Breath", "condition_name": "Heart Attack", "confidence": 80},
        {"symptom_name": "Nausea", "condition_name": "Heart Attack", "confidence": 60},
        
        # Stroke mappings
        {"symptom_name": "Numbness", "condition_name": "Stroke", "confidence": 85},
        {"symptom_name": "Vision Problems", "condition_name": "Stroke", "confidence": 75},
        {"symptom_name": "Dizziness", "condition_name": "Stroke", "confidence": 70},
        
        # Asthma mappings
        {"symptom_name": "Wheezing", "condition_name": "Asthma", "confidence": 85},
        {"symptom_name": "Shortness of Breath", "condition_name": "Asthma", "confidence": 80},
        {"symptom_name": "Chest Tightness", "condition_name": "Asthma", "confidence": 75},
        
        # Flu mappings
        {"symptom_name": "Fever", "condition_name": "Flu", "confidence": 80},
        {"symptom_name": "Fatigue", "condition_name": "Flu", "confidence": 70},
        {"symptom_name": "Cough", "condition_name": "Flu", "confidence": 65},
    ]
    
    for mapping in mappings:
        symptom = next(s for s in symptoms if s.name == mapping["symptom_name"])
        condition = next(c for c in conditions if c.name == mapping["condition_name"])
        
        mapping_obj = SymptomConditionMapping(
            symptom_id=symptom.id,
            condition_id=condition.id,
            confidence_score=mapping["confidence"]
        )
        db.add(mapping_obj)
    
    db.commit()
    print(f"✅ Added {len(mappings)} symptom-condition mappings")
    db.close()

if __name__ == "__main__":
    add_medical_knowledge()