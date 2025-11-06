# api/face_auth_routes.py
import cv2
import numpy as np
import base64
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from processors.face_processor import FaceRecognitionService

router = APIRouter(prefix="/api/face-auth")
face_service = FaceRecognitionService()

logger = logging.getLogger(__name__)

def decode_image_data(image_data: str):
    """Decode base64 image data"""
    try:
        if 'base64,' in image_data:
            image_data = image_data.split('base64,')[1]
        
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        return frame if frame is not None else None
        
    except Exception as e:
        logger.error(f"Image decoding error: {str(e)}")
        return None

@router.websocket("/ws/face-auth")
async def face_auth_websocket(websocket: WebSocket):
    """WebSocket for face authentication"""
    await websocket.accept()
    logger.info("Face auth WebSocket connected")
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message['type'] == 'frame':
                try:
                    # Decode image
                    frame = decode_image_data(message['data'])
                    
                    if frame is None:
                        await websocket.send_json({
                            "type": "face_detection",
                            "face_detected": False,
                            "timestamp": message.get('timestamp')
                        })
                        continue
                    
                    # Recognize user
                    auth_result = face_service.recognize_user(frame)
                    
                    # Determine face detection
                    face_detected = (
                        auth_result.get('success', False) or 
                        'No face detected' not in auth_result.get('message', '')
                    )
                    
                    response = {
                        "type": "face_detection",
                        "face_detected": face_detected,
                        "timestamp": message.get('timestamp'),
                        "authentication": auth_result
                    }
                    
                    await websocket.send_json(response)
                    
                except Exception as e:
                    logger.error(f"Error processing frame: {e}")
                    await websocket.send_json({
                        "type": "face_detection",
                        "face_detected": False,
                        "timestamp": message.get('timestamp')
                    })
            
            elif message['type'] == 'register':
                try:
                    username = message['username']
                    
                    if 'data' not in message:
                        await websocket.send_json({
                            "type": "registration_result",
                            "success": False,
                            "message": "No face data provided"
                        })
                        continue
                    
                    # Decode registration image
                    frame = decode_image_data(message['data'])
                    
                    if frame is None:
                        await websocket.send_json({
                            "type": "registration_result",
                            "success": False,
                            "message": "Failed to process image"
                        })
                        continue
                    
                    # Register user
                    register_result = face_service.register_user(username, frame)
                    await websocket.send_json({
                        "type": "registration_result",
                        **register_result
                    })
                        
                except Exception as e:
                    logger.error(f"Error during registration: {e}")
                    await websocket.send_json({
                        "type": "registration_result",
                        "success": False,
                        "message": f"Registration failed: {str(e)}"
                    })
                
    except WebSocketDisconnect:
        logger.info("Face auth WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error in face auth WebSocket: {e}")
        await websocket.close()

@router.get("/users")
async def get_all_users():
    """Get all registered users"""
    users = face_service.get_all_users()
    return {"users": users}

@router.get("/users/{username}")
async def get_user(username: str):
    """Get user data"""
    user_data = face_service.get_user_data(username)
    if not user_data:
        return {"error": "User not found"}
    return user_data