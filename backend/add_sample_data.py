#!/usr/bin/env python3
"""
Add sample doctor data to the database
"""
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import SessionLocal
from app.models.doctor import Doctor

def add_sample_doctors():
    db = SessionLocal()
    
    # Check if data already exists
    existing_count = db.query(Doctor).count()
    if existing_count > 0:
        print(f"✅ Database already has {existing_count} doctors. Skipping sample data.")
        db.close()
        return
    
    sample_doctors = [
        Doctor(
            name="Dr. Sarah Chen",
            specialty="Cardiologist",
            contact="+1-555-0101",
            address="123 Heart Lane, Suite 100",
            city="New York",
            latitude=40.7128,
            longitude=-74.0060
        ),
        Doctor(
            name="Dr. Michael Rodriguez",
            specialty="Neurologist", 
            contact="+1-555-0102",
            address="456 Brain Street, Floor 3",
            city="Los Angeles",
            latitude=34.0522,
            longitude=-118.2437
        ),
        Doctor(
            name="Dr. Emily Watson",
            specialty="General Physician",
            contact="+1-555-0103", 
            address="789 Health Ave, Building A",
            city="Chicago",
            latitude=41.8781,
            longitude=-87.6298
        ),
        Doctor(
            name="Dr. James Kim",
            specialty="Pulmonologist",
            contact="+1-555-0104",
            address="321 Lung Road, Unit 205",
            city="Houston", 
            latitude=29.7604,
            longitude=-95.3698
        ),
        Doctor(
            name="Dr. Lisa Thompson",
            specialty="Dermatologist",
            contact="+1-555-0105",
            address="654 Skin Court, Office 12",
            city="Phoenix",
            latitude=33.4484,
            longitude=-112.0740
        )
    ]
    
    try:
        db.add_all(sample_doctors)
        db.commit()
        print("✅ Sample doctors added successfully!")
        print(f"Added {len(sample_doctors)} doctors to the database.")
        print("\n📋 Added doctors:")
        for doctor in sample_doctors:
            print(f"   - {doctor.name} ({doctor.specialty})")
    except Exception as e:
        db.rollback()
        print(f"❌ Error adding sample doctors: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    add_sample_doctors()