# GreenWall LLM Integration

A voice-interactive Vertical Living Green Wall system powered by AI that enables natural conversations between plants and humans. This project combines IoT sensors, speech recognition, and Large Language Models to create an intelligent plant monitoring and interaction system.

## 🌿 Project Overview

This thesis project demonstrates an innovative approach to human-plant interaction by giving a vertical green wall the ability to:
- **Communicate** its water needs through voice
- **Respond** to user questions about its health and status
- **Detect** human presence and initiate conversations
- **Monitor** soil moisture levels in real-time

The system consists of two main components that work together over a network connection:
- **Raspberry Pi Client** (`pi_greenwall_client.py`) - Handles sensors, audio I/O, and user interaction
- **Brain Server** (`brain_server.py`) - Processes speech, runs AI conversations, and manages logic

## 🏗️ System Architecture

```
┌─────────────────────────────────────┐
│      Raspberry Pi Client            │
│  ┌────────────────────────────┐     │
│  │  • PIR Motion Sensor       │     │
│  │  • Soil Moisture Sensor    │     │
│  │  • Microphone (Audio In)   │     │
│  │  • Speaker (Audio Out)     │     │
│  └────────────────────────────┘     │
└─────────────┬───────────────────────┘
              │ Socket Connection
              │ (JSON + Binary Packets)
              ▼
┌─────────────────────────────────────┐
│        Brain Server (PC)            │
│  ┌────────────────────────────┐     │
│  │  • Speech Recognition      │     │
│  │  • LLM (Ollama/Gemma2)     │     │
│  │  • Text-to-Speech (gTTS)   │     │
│  │  • Conversation Logic      │     │
│  └────────────────────────────┘     │
└─────────────────────────────────────┘
```

## ✨ Features

### Core Functionality
- **Motion-Triggered Interaction**: Detects hand waves via PIR sensor to initiate conversations
- **Voice-Based Communication**: Natural speech input/output for seamless interaction
- **Soil Moisture Monitoring**: Real-time monitoring with intelligent water request system
- **Conversational AI**: Context-aware chat powered by Ollama (Gemma2:2b model)
- **Adaptive Responses**: Different conversation flows based on plant health status

### Technical Highlights
- Custom binary protocol for efficient audio streaming
- Multi-threaded sensor monitoring
- Robust error handling and automatic reconnection
- Real-time sensor data integration during conversations
- Text cleaning for natural-sounding speech synthesis

## 🛠️ Hardware Requirements

### Raspberry Pi Client
- Raspberry Pi (3/4/Zero 2W recommended)
- PIR Motion Sensor (connected to Arduino)
- Soil Moisture Sensor (connected to Arduino)
- USB Microphone
- Speaker or 3.5mm audio output
- Arduino (for sensor interfacing via `/dev/ttyACM1`)

### Server Machine
- PC/Laptop with Python 3.x
- Network connectivity to Raspberry Pi

## 📦 Software Dependencies

### Raspberry Pi Client (`pi_greenwall_client.py`)
```bash
pip install pyserial
```

**System Tools Required:**
- `arecord` (ALSA audio recording)
- `mpg123` (MP3 audio playback)

### Brain Server (`brain_server.py`)
```bash
pip install speechrecognition
pip install gtts
pip install ollama
```

**Additional Requirements:**
- [Ollama](https://ollama.ai/) installed with `gemma2:2b` model
```bash
ollama pull gemma2:2b
```

## ⚙️ Configuration

### Client Configuration
Edit `pi_greenwall_client.py`:
```python
SERVER_IP = '192.168.137.1'  # IP address of Brain Server
PORT = 5000                   # Must match server port
SERIAL_PORT = '/dev/ttyACM1'  # Arduino serial port
BAUD_RATE = 9600
MIC_DEVICE = "plughw:1,0"     # ALSA microphone device
```

### Server Configuration
Edit `brain_server.py`:
```python
HOST_IP = '10.32.38.101'  # Server's IP address
PORT = 5000                # Must match client port
```

### Finding Your ALSA Audio Device
On Raspberry Pi:
```bash
arecord -l                 # List recording devices
aplay -l                   # List playback devices
```

## 🚀 Running the System

### 1. Start the Brain Server (PC/Laptop)
```bash
python brain_server.py
```

### 2. Start the Client (Raspberry Pi)
```bash
python pi_greenwall_client.py
```

### 3. Interaction Flow
1. **Wave Detection**: Wave your hand near the PIR sensor
2. **Introduction**: The wall introduces itself and reports soil status
3. **User Prompt**: Press ENTER when ready to speak
4. **Conversation**: Speak naturally after hearing the response tone
5. **Exit**: Say "bye", "stop", or "exit" to end the session

## 🔄 Communication Protocol

The system uses a custom packet-based protocol:

### Packet Types

| Packet Type | Direction | Purpose |
|------------|-----------|---------|
| `PIR_TRIGGER` | Client → Server | Motion detected with soil data |
| `SPEAK_INTRO` | Server → Client | Intro audio (no recording) |
| `SPEAK` | Server → Client | Response audio + record user |
| `AUDIO` | Client → Server | User's recorded voice |
| `GET_SOIL` | Server → Client | Request current soil data |
| `SOIL_DATA` | Client → Server | Current soil moisture level |
| `USER_ENTER` | Client → Server | User pressed ENTER key |
| `END_SESSION` | Server → Client | Conversation ended |

### Packet Structure
```json
{
  "type": "MESSAGE_TYPE",
  "file_size": 0,
  "payload": {}
}
```

## 🧪 Testing Components

The repository includes test utilities:

- `test_microphone.py` - Verify microphone recording functionality
- `test_pir.py` - Test PIR motion sensor
- `check_Sensor.py` - Arduino sensor diagnostics

## 📁 Project Structure

```
GreenWall_LLM/
├── pi_greenwall_client.py    # Raspberry Pi client
├── brain_server.py            # AI server
├── test_microphone.py         # Microphone test utility
├── test_pir.py                # PIR sensor test
├── check_Sensor.py            # Sensor diagnostics
├── FIREWALL_SETUP.md          # Network configuration guide
├── intro.mp3                  # Pre-recorded intro audio
├── goodbye.mp3                # Pre-recorded goodbye audio
├── .venv/                     # Python virtual environment
└── backup/                    # Backup files
```

## 🔧 Troubleshooting

### Connection Issues
- Ensure both devices are on the same network
- Check firewall settings (see `FIREWALL_SETUP.md`)
- Verify IP addresses in configuration match actual IPs

### Audio Issues
- Test microphone: `arecord -D plughw:1,0 -d 5 test.wav`
- Test speaker: `mpg123 intro.mp3`
- Check ALSA device names with `arecord -l`

### Sensor Issues
- Verify Arduino connection: `ls /dev/ttyACM*`
- Test serial communication: `python check_Sensor.py`
- Check baud rate matches Arduino sketch

### LLM Issues
- Ensure Ollama is running: `ollama serve`
- Verify model is available: `ollama list`
- Pull model if needed: `ollama pull gemma2:2b`

## 🎓 Thesis Context

This project is part of a thesis exploring human-computer interaction in the context of smart agriculture and IoT. The goal is to investigate how conversational AI can enhance plant care and user engagement with urban greenery systems.

**Key Research Questions:**
- Can voice interaction improve user awareness of plant health?
- How do users respond to plants that "communicate" their needs?
- What is the effectiveness of LLMs in creating natural plant personas?

## 🔐 Security Notes

- The current implementation uses unencrypted sockets for local network communication
- For production deployments, consider adding:
  - TLS/SSL encryption for network traffic
  - Authentication for server connections
  - Environment variables for sensitive configuration

## 📝 License

This project is part of academic research at Stockholm University.

## 👤 Author

Chaluka - Stockholm University, Spring 2025 Thesis Project

## 🙏 Acknowledgments

- **Ollama** - For providing local LLM capabilities
- **Google Text-to-Speech (gTTS)** - For speech synthesis
- **SpeechRecognition** - For audio transcription
- Stockholm University - For academic support

## 📚 Future Improvements

- [ ] Implement voice activity detection to replace manual ENTER key
- [ ] Add support for multiple plant sensors
- [ ] Create web dashboard for monitoring
- [ ] Implement conversation history logging
- [ ] Add support for additional languages
- [ ] Integrate weather data for smarter recommendations
- [ ] Deploy edge AI (on-device LLM) to reduce latency

---

**For questions or collaboration, please open an issue on GitHub.**
