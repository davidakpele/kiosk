# 🏥 AI Medical Kiosk - Real-Time Physiological Monitor

A cutting-edge medical kiosk system that performs non-contact physiological monitoring using computer vision and AI. This system captures live camera feed and analyzes vital signs in real-time without any physical contact.

## 🎥 Live Demo

![Medical Kiosk in Action](./static/video.mp4)
## 🚀 Features

### ✅ Currently Implemented
- **Real-time Camera Processing**: 720p/1080p live video streaming
- **Face Detection & Landmark Tracking**: MediaPipe with 468 facial points
- **Heart Rate Monitoring**: rPPG (remote Photoplethysmography) technology
- **Stress Level Analysis**: Multi-parameter stress assessment
- **Fatigue Risk Detection**: Trend-based fatigue analysis
- **Live Web Dashboard**: Real-time metrics and alerts
- **WebSocket Integration**: Seamless real-time communication
- **Medical Alert System**: Automatic health status notifications

### 🔬 Technical Capabilities
- **Heart Rate Accuracy**: Professional-grade rPPG algorithm
- **Stress Index**: Comprehensive multi-signal analysis
- **Real-time Processing**: 30 FPS with minimal latency
- **Confidence Scoring**: Signal quality assessment

## 🛠 Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **WebSockets** - Real-time bidirectional communication
- **OpenCV** - Computer vision processing
- **MediaPipe** - Face mesh and landmark detection
- **NumPy/SciPy** - Signal processing and analysis
- **PostgreSQL** - Medical data storage (ready for integration)

### Frontend
- **HTML5/CSS3/JavaScript** - Responsive web interface
- **Real-time Updates** - Live video streaming and metrics
- **Medical-grade UI** - Professional healthcare interface

### AI/ML
- **rPPG Algorithm** - Remote heart rate detection
- **FFT Analysis** - Frequency domain signal processing
- **Bandpass Filtering** - Noise reduction and signal cleaning
- **Peak Detection** - Heart rate variability analysis

## 📁 Project Structure

```
medical-kiosk/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── core/
│   │   ├── camera.py           # Camera management
│   │   ├── face_processor.py   # MediaPipe face detection
│   │   ├── rppg_processor.py   # Heart rate analysis
│   │   └── post_processor.py   # Medical analysis
│   └── database/              # PostgreSQL integration ready
├── requirements.txt
└── README.md
```

## 🎯 How It Works

1. **Video Capture**: Live camera feed at 30 FPS
2. **Face Detection**: MediaPipe identifies facial landmarks
3. **ROI Extraction**: Forehead region isolated for rPPG
4. **Signal Processing**: Green channel analysis for blood volume changes
5. **Heart Rate Calculation**: FFT analysis in frequency domain
6. **Medical Analysis**: Stress, fatigue, and health status assessment
7. **Real-time Display**: Live results on web dashboard

## 🚀 Quick Start

### Installation
```bash
# Clone and setup
pip install -r requirements.txt

# Start the application
uvicorn app.main:app --reload --port 8000
```

### Access Points
- **Web Interface**: `http://localhost:8000/monitor`
- **API Documentation**: `http://localhost:8000/docs`
- **WebSocket**: `ws://localhost:8000/ws/{session_id}`

## 📊 API Endpoints

### HTTP Endpoints
- `GET /` - API status
- `POST /api/sessions/start` - Start monitoring session
- `POST /api/sessions/{id}/stop` - Stop monitoring session
- `GET /monitor` - Web interface

### WebSocket
- `WS /ws/{session_id}` - Real-time video and data streaming

## 🔬 Medical Metrics

### Current Measurements
- **Heart Rate**: 40-180 BPM range with confidence scoring
- **Stress Index**: 0-1.0 scale based on multiple parameters
- **Fatigue Risk**: Low/Medium/High classification
- **Health Status**: Normal/Caution/Warning assessment

### Alert System
- Elevated heart rate detection
- High stress level warnings
- Fatigue risk notifications
- Signal quality monitoring

## 🎨 Web Interface Features

- **Live Video Feed**: Real-time camera preview with face landmarks
- **Medical Dashboard**: Comprehensive vital signs display
- **Alert System**: Color-coded medical notifications
- **Session Management**: Start/stop monitoring controls
- **Responsive Design**: Works on desktop and mobile

## 🔄 Real-time Processing Pipeline

```
Camera → OpenCV → MediaPipe Face Mesh → ROI Extraction → 
rPPG Signal → FFT Analysis → Heart Rate → Medical Analysis → 
WebSocket → Web Dashboard
```

## 🏗 Architecture Highlights

- **Modular Design**: Separated concerns for easy maintenance
- **Real-time Performance**: Optimized for 30 FPS processing
- **Scalable Backend**: FastAPI with async capabilities
- **Professional Grade**: Medical-level signal processing
- **Extensible**: Ready for additional health metrics

## 🔮 Next Phase Development

### Planned Enhancements
- **Medical AI Integration**: Ollama models (Good Doctor, MedGemma)
- **Respiratory Rate**: Breathing pattern analysis
- **HRV Analysis**: Heart rate variability metrics
- **Patient Records**: PostgreSQL database integration
- **Multi-person Support**: Simultaneous multiple patient monitoring
- **Mobile App**: iOS/Android companion application

### Advanced Features
- **Historical Trend Analysis**: Long-term health tracking
- **Report Generation**: Comprehensive patient reports
- **Telemedicine Integration**: Remote doctor consultations
- **Emergency Alerts**: Automated emergency services notification

## 🎯 Achievement Summary

✅ **Complete Foundation**
- Real-time video processing pipeline
- Professional medical analysis algorithms
- Production-ready web interface
- Scalable backend architecture

✅ **Advanced Computer Vision**
- Accurate face detection and tracking
- Robust rPPG signal extraction
- Noise-resistant signal processing
- Real-time performance optimization

✅ **Medical-Grade Analytics**
- Accurate heart rate monitoring
- Comprehensive stress assessment
- Intelligent fatigue detection
- Professional alert system

## 🤝 Contributing

This project demonstrates the power of AI-assisted development in creating sophisticated medical technology systems. The architecture is designed for easy extension and collaboration.

## 📄 License

Medical-grade system built for healthcare innovation and research purposes.

---

**Built with cutting-edge AI agents - revolutionizing accessible healthcare through computer vision and real-time analytics!** 🚀❤️