import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel
from llama_cpp import Llama
import subprocess
import queue
import time
import os
import signal
import sys


sd.default.device = None 
stop_flag = None
""" Setting """
WHISPER_MODEL = WhisperModel("tiny.en",device="cpu",compute_type="int8")
SAMPLE_RATE = 16000
BLOCK_SIZE = 1024
BUFFER_SECONDS = 2
buffer = []
LLAMA_MODEL_PATH = "Meta-Llama-3-8B-Instruct.Q2_K.gguf"
llm = Llama(model_path=LLAMA_MODEL_PATH, n_threads=8)
PIPER_MODEL = "piper/models/en_US-lessac-high.onnx"

audio_queue =  queue.Queue()
recording = False

"""Hard exit for ctrl+c"""
def signal_handler(sig,frame):
    global stop_flag
    stop_flag=True
    print("\n🛑 Stopping immediately...")
signal.signal(signal.SIGINT,signal_handler)

""" Text to speech"""
def voice_output(text):
    print("🔊 Speaking:",text)
    cmd = [
        "piper",
        "--model",PIPER_MODEL,
        "--output_file","response.wav",
        "--length-scale","0.7"

    ]

    p = subprocess.Popen(cmd,stdin=subprocess.PIPE)
    p.stdin.write(text.encode("utf-8"))
    p.stdin.close()
    p.wait()
    os.system("start response.wav")

""" Speech to text"""
def transcribe_audio(audio_data):
    print("🎧 Listening...")
    segments, _ = WHISPER_MODEL.transcribe(
        audio_data,
        vad_filter=True,
        vad_parameters={"threshold": 0.4},
        beam_size=5,
        language="en"
    )
    if _.language_probability < 0.50:
        return ""
    text = " ".join(seg.text.strip() for seg in segments)
    return text.lower().strip()


"""LLm comes here and delive the answer to the user main loop"""
def process_audio():
    print("\n🎤 Jarvis Ready! Speak every 2 seconds...")

    try:
        while not stop_flag:
            frame = sd.rec(
                int(SAMPLE_RATE * BUFFER_SECONDS),
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="int16"
            )
            sd.wait()

            audio_data = frame[:, 0].astype(np.float32) / 32768.0
            text = transcribe_audio(audio_data)

            if stop_flag:
                break

            if len(text) < 2:
                continue

            print("👂 You:", text)

           

            response = llm(
                f"Act like a professional voice assistant named Lessac.\n"
                f"Rules:\n"
                f"- Reply in 1 short sentence.\n"
                f"- No filler words.\n"
                f"- No long explanations.\n"
                f"- If greeting like 'hello', respond politely and ask how you can help.\n"
                f"- If unclear speech, say 'Can you repeat that?'\n"
                f"User said: {text}\n"
                f"Lessac:", max_tokens=30)["choices"][0]["text"].strip()
            

            print("🤖 Lessac:", response)
            voice_output(response)

    except Exception as e:
        print("⚠ Error:", e)
    finally:
        print("👋 Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    process_audio()