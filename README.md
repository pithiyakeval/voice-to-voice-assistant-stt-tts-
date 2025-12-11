# 🤖 Aeron — Offline Voice-to-Voice AI Assistant

Aeron is a fully **offline**, **real-time** AI voice assistant built using:

- **Porcupine** → Wake Word ("Hey Aeron")
- **Whisper (faster-whisper)** → Speech-to-Text
- **Ollama (phi3)** → Local LLM reasoning
- **Piper TTS** → Natural voice output
- **PyAudio** → Live microphone capture

Aeron runs **100% offline** and can:

- Wake on **"Hey Aeron"**
- Understand spoken commands
- Perform basic actions (open Chrome, YouTube, tell time/date, etc.)
- Generate intelligent short responses using LLM
- Speak replies using Piper TTS

---

## 🚀 Features

### 🔊 Wake Word Detection
- Powered by **Picovoice Porcupine**
- Custom keyword: **"Hey Aeron"**

### 🗣 Speech Recognition (STT)
- Uses **Whisper tiny.en**
- Very fast with **faster-whisper**

### 🧠 LLM Response Generation
- Runs **Ollama** locally (phi3 by default)
- Generates short, polished replies

### 🔉 Text-to-Speech (TTS)
- Uses **Piper TTS ONNX models**
- Produces natural, low-latency speech

### 🎤 Real-Time Audio Pipeline
- Continuous mic listening
- Wake → STT → LLM → TTS → Playback

---

## 📦 Installation

Clone the repository:

```bash
git clone https://github.com/pithiyakeval/voice-to-voice-assistant-stt-tts-.git
cd voice-to-voice-assistant-stt-tts-
Install dependencies:

bash
Copy code
pip install -r requirements.txt
📥 Model Downloads (Required)
These files are NOT included in the repo — download them manually.

🔸 Whisper STT Model
Download tiny model:

https://huggingface.co/ggerganov/whisper.cpp

Put inside:

bash
Copy code
ai/whisper/
🔸 Piper TTS Model
Download voice model:

https://github.com/rhasspy/piper/releases

Put inside:

Copy code
piper-models/
🔸 Porcupine Wake Word
Generate wake-word model (“Hey Aeron”):

https://console.picovoice.ai/

Put inside:

bash
Copy code
ai/porcupine/
🔸 Ollama Model (phi3)
Install Ollama:
https://ollama.com/

Pull model:

bash
Copy code
ollama pull phi3
▶️ Running Aeron
bash
Copy code
python main.py
Aeron will:

1️⃣ Listen for wake word → “Hey Aeron”
2️⃣ Convert your speech to text
3️⃣ Send text to local LLM (phi3)
4️⃣ Speak the response using Piper

📁 Project Structure
bash
Copy code
assistant-practice/
│
├── main.py
├── jarvis.py
├── requirements.txt
├── .gitignore
├── README.md
│
├── ai/
│   ├── whisper/         # Whisper tiny model
│   ├── porcupine/       # Wake word model
│
├── llm_model/           # Custom GGUF (optional)
├── piper-models/        # Piper TTS voice
└── certs/               # SSL (ignored)
📝 Notes
All ML models are ignored via .gitignore.

Repo stays clean and lightweight.

Fully offline operation supported.

Works on Windows, Linux, and macOS.

🔧 Future Improvements
Multi-command execution

Task memory

GUI interface

Faster TTS with CUDA

Support for Hindi/Gujarati STT

💡 Want to Contribute?
Feel free to open an issue or submit a PR!

yaml
Copy code

---

# ✅ NEXT STEP
Commit this to GitHub:

```bash
git add README.md
git commit -m "Add complete project documentation"
git push
