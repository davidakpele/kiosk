#!/usr/bin/env python3
"""
Test script to verify all packages are installed correctly
"""

try:
    from fastapi import FastAPI
    print("FastAPI installed successfully")
except ImportError as e:
    print(f"FastAPI installation failed: {e}")

try:
    import sqlalchemy
    print("SQLAlchemy installed successfully")
except ImportError as e:
    print(f"SQLAlchemy installation failed: {e}")

try:
    import uvicorn
    print("Uvicorn installed successfully")
except ImportError as e:
    print(f"Uvicorn installation failed: {e}")

try:
    import pytest
    print("Pytest installed successfully")
except ImportError as e:
    print(f"Pytest installation failed: {e}")

print("\nPackage installation test completed!")