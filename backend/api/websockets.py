# api/routes.py
import asyncio
import time
from fastapi import WebSocket, WebSocketDisconnect

from api.routes import monitoring_sessions

async def websocket_endpoint(websocket: WebSocket, session_id: str):
    if session_id not in monitoring_sessions:
        await websocket.close(code=1008, reason="Session not found")
        return
        
    monitoring_session = monitoring_sessions[session_id]
    await websocket.accept()
    
    try:
        while monitoring_session.is_running:
            start_time = time.time()
            
            # Continuous processing - no blocking
            result = await monitoring_session.process_frame()  # Now async
            
            if result:
                await websocket.send_json(result)
            
            # Maintain smooth 30 FPS with precise timing
            processing_time = time.time() - start_time
            sleep_time = max(0.001, (1/30) - processing_time)
            
            await asyncio.sleep(sleep_time)
            
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        print(f"Error in WebSocket: {e}")
    finally:
        await websocket.close()

def register_websocket_handlers(app):
    @app.websocket("/ws/{session_id}")
    async def websocket_handler(websocket: WebSocket, session_id: str):
        await websocket_endpoint(websocket, session_id)