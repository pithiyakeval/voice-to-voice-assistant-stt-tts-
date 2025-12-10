import os
import sys
import signal
import time
import subprocess
import webbrowser
from datetime import datetime
import pvporcupine

import numpy as np
import pyaudio
import requests
from faster_whisper import WhisperModel


def beep():
    print("\a")


WAKEWORD_PATH = "Hey-Aeron_en_windows_v3_0_0.ppn"
#============================= Porcupine picovoice access key ==================
ACCESS_KEY = "oGU55Ev+HksFPpTithsFrm8eaH7f6SdZ/wTrfW5Aeoz3aFi5mhGsOg=="
MIC_INDEX = 1
# ========= GLOBAL CONFIG   ===============

stop_flag = False

#Audio / STT 
SAMPLE_RATE = 16000
BLOCK_SIZE = 1024
BUFFER_SECONDS = 2


#Whisper model (tiny.en/base.en)
WHISPER_MODEL_NAME = "tiny.en"
WHISPER_MODEL = WhisperModel(
    WHISPER_MODEL_NAME,
    device="cpu",
    compute_type="int8"
)



#LLM CALLING =======

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "phi3"


#Piper (TTS) ======
PIPER_EXE = "piper"
PIPER_MODEL = "piper-models/en_US-lessac-high.onnx"




# Emergency stopping with ctrl+c or in case u called Aeron accidently 
def signal_handler(sig,frame):
    global stop_flag
    stop_flag = True
    print("\n🛑 Stopping Aeron... ")
signal.signal(signal.SIGINT,signal_handler)


#======= short reply only not sentences ===== 
def shorten_reply(text:str,max_words : int = 15,)-> str:
    if not text:
        return ""
    words = text.strip().split()
    if len(words) <= max_words:
        return text.strip()
    return " ".join(words[:max_words]).strip()

#======== TTS (piper) ======

def voice_output(text: str):
    text = text.strip()
    if not text:
        return
    
    print("🔊 Aeron:", text)

    temp_wav = "Aeron_response.wav"
    cmd = [
        PIPER_EXE,
        "--model", PIPER_MODEL,
        "--output_file", temp_wav,
        "--length-scale", "1.05",
        "--noise-scale", "0.55",
        "--noise-w-scale", "0.7"
    ]

    try:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        p.stdin.write(text.encode("utf-8"))
        p.stdin.close()
        p.wait()

        os.system(f'start {temp_wav}')  # replaces os.startfile for safer async

    except Exception as e:
        print("⚠ TTS error:", e)

#====== audio capture pyaudio ========4

def create_input_stream(pa:pyaudio.PyAudio):
    """create a pyAudio input stream."""
    stream = pa.open(
        format = pyaudio.paInt16,
        channels = 1,
        rate = SAMPLE_RATE,
        input = True,
        frames_per_buffer = BLOCK_SIZE
    )
    return stream

def rec_chunk(stream,seconds: int = BUFFER_SECONDS)-> np.ndarray:
    """record audio chunk of given seconds and return as float32 numpy arr."""
    num_frames = int(SAMPLE_RATE/BLOCK_SIZE*seconds)
    frames = []

    for _ in range(num_frames):
        try:
            data = stream.read(BLOCK_SIZE,exception_on_overflow=False)
        except Exception as e:
            print(" AUDIO read error",e)
            return np.array([],dtype=np.float32)
        frames.append(np.frombuffer(data,dtype=np.int16))
    if not frames:
        return np.array([],dtype=np.float32)
    
    audio_int16 = np.concatenate(frames)
    audio_float32 = audio_int16.astype(np.float32) / 32768.0
    return audio_float32

#======= stt (whisper) ======

def transcribe_audio(audio_data:np.ndarray)-> str:
    """transcribe a single audio chunk using faster whisper."""
    if audio_data is None or len(audio_data) == 0:
        return ""
    print("🎧 Transcribing...")
    try:
        segments, info = WHISPER_MODEL.transcribe(
            audio_data,
            beam_size=1,
            vad_filter=True,
            vad_parameters={"threshold":0.4},
            language="en"
        )
    except Exception as e:
        print("Whisper error:",e)
        return ""
    if getattr(info, "language_probability",1.0)<0.40:
        return ""
    
    text = " ".join(seg.text.strip() for seg in segments)
    text = text.lower().strip()
    return text

# ======= actions ======

def handle_intent(text:str):
    cmd = text.lower()

    global stop_flag

    #power off
    if any(x in cmd for x in ["stop Aeron","exit Aeron","shutdown","power off"]):
        stop_flag = True
        return "system offline"
    #greetings    
    # Fixed & more intelligent greeting rule
    if cmd in ["hello", "hi", "hey", "hey aeron", "aeron"]:
        return "Hello Keval. How can I help?"

    #youtube
    if "youtube" in cmd:
        webbrowser.open("https://www.youtube.com")
        return "Youtube open"
    #music
    if "play" in cmd and ("music" in cmd or "song" in cmd):
        webbrowser.open("https://open.spotify.com/")
        return "Music opened"
    #chrome
    if "chrome" in cmd:
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if os.path.exists(chrome_path):
            subprocess.Popen([chrome_path])
            return "Chrome open."
        return "Chrome not found."
    

    #time
    if "time" in cmd:
       now = datetime.now().strftime("%I:%M %p")
       return f"Keval, the time is {now}"
    #date
    if "date" in cmd:
        today = datetime.now().strftime("%d %B %Y")
        return f"Keval, today is {today}"
    #volume conrol
    if "volume up " in cmd:
        os.system("nircmd.exe changesysvolume 5000")
        return "Volume up."
    if "volume down" in cmd:
        os.system("nircmd.exe changesysvolume -5000")
        return "Volume down"
    
    # SHAYARI
    if "shayari" in cmd or "poetry" in cmd:
            return "Dil ke armaan, labo par aa gaye. Bewajah aansu, saath chal pade."

        # JOKES
    if "joke" in cmd:
            return "Why don’t robots panic? We have great processors!"

    return None 


# ================ LLM(OLLAMA) ==========

def ask_llm(user_text:str)->str:
    """
    Call Ollama to generate short assistant-style answer.
    Uses /api/generate endpoint simple.

     """
    system_prompt = (
        "Your name is Aeron — a fast & professional AI assistant.\n"
        "Guidelines:\n"
        "- Keep responses under 10 words.\n"
        "- Direct. Confident. No filler.\n"
        "- One short sentence only.\n"
        "- If user greets: “Good day. How may I assist you?”\n"
        "- If you did not understand, say: “Pardon me. Could you rephrase it?”\n"
        "- Never say 'as an AI model'.\n"
        "Rules:\n"
        "- If user asks knowledge (weather, facts, advice, etc.), reply clearly with 1–2 sentences.\n"
        "- If user gives a device control request like open or play, reply short: 'Done.'\n"
        "- Tone: friendly, helpful, confident.\n"
        "- Speak naturally.\n"
    )

    full_prompt = (
        f"{system_prompt}\n\n"
        f"User: {user_text}\n"
        f"Aeron:"
    )

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": full_prompt,
        "stream": False
    }


    try:
            resp = requests.post(OLLAMA_URL, json=payload, timeout=30)
            resp.raise_for_status()
            reply = resp.json().get("response", "").strip()
            return shorten_reply(reply)
    except Exception:
        return "I am having trouble thinking right now, but I am still here."


#===== wake up word jarvis=============================================================

def listen_for_wake_word(pa: pyaudio.PyAudio):
    try:
        porcupine = pvporcupine.create(
    access_key=ACCESS_KEY,
    keyword_paths=["piper-models/Hey-Aeron_en_windows_v3_0_0.ppn"]
)


        print("🎧 Say 'Hey Aeron' (10 sec timeout)...")


    except Exception as e:
        print("❌ Porcupine init failed:", e)
        return False

    try:
        stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            input_device_index=MIC_INDEX,
            frames_per_buffer=porcupine.frame_length
        )
    except Exception as e:
        print("❌ Mic stream open failed:", e)
        porcupine.delete()
        return False

    

    start_time = time.time()
    wake_detected = False

    try:
        while not stop_flag:
            if time.time() - start_time > 10:
                print("⏳ Timeout: No wake word detected")
                voice_output("I'll be here if you need me.")
                break

            try:
                pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
            except IOError:
                continue

            pcm = np.frombuffer(pcm, dtype=np.int16)
            result = porcupine.process(pcm)

            if result >= 0:
                print("🟢 Wake word detected!")
                wake_detected = True
                break

    except Exception as e:
        print("⚠ Wake word loop error:", e)

    # IMPORTANT FIX: Release mic before command mode!
    stream.stop_stream()
    stream.close()
    porcupine.delete()
    time.sleep(0.1)  # small pause for driver to reset

    if wake_detected:
        beep()  # activation sound
        print("🎤 Listening...")
        return True
    else:
        return False


def listen_for_command(pa: pyaudio.PyAudio, timeout=5):
    stream = pa.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE,
        input=True,
        input_device_index=MIC_INDEX,
        frames_per_buffer=BLOCK_SIZE
    )

    print("🎙 Tell me what can i do for you?")

    frames = []
    start_time = time.time()

    while not stop_flag:
        try:
            pcm = stream.read(BLOCK_SIZE, exception_on_overflow=False)
        except IOError:
            continue
        
        frames.append(np.frombuffer(pcm, dtype=np.int16))

        # Stop listening after timeout seconds
        if time.time() - start_time > timeout:
            break

    stream.stop_stream()
    stream.close()

    if len(frames) == 0:
        return ""

    audio_data = np.concatenate(frames).astype(np.float32) / 32768.0
    return transcribe_audio(audio_data)

#========= MAIB LOOP ==========

def main():
    print("🤖 Aeron Ready — Say 'Hey Aeron' to wake him up 💡")
    print("Hit CTRL + C to exit.\n")

    pa = pyaudio.PyAudio()

    try:
        while not stop_flag:
            # Wake word wait
            activated = listen_for_wake_word(pa)
            if not activated or stop_flag:
                break

            beep()
            print("🎙 Aeron is listening...")

            text = listen_for_command(pa, timeout=6)

            if stop_flag:
                break

            if not text:
                voice_output("Pardon me. Could you rephrase it?")
                print("🔄 Back to Wake Mode...\n")
                continue

            print(f"👂 You: {text}")

            # Intent first
            action_reply = handle_intent(text)
            if action_reply:
                voice_output(action_reply)
                print("🔄 Back to Wake Mode...\n")
                continue

            # Not a known action → AI model
            reply = ask_llm(text)
            voice_output(reply)

            print("🔄 Back to Wake Mode...\n")

    except KeyboardInterrupt:
        print("\n🛑 Stopping Aeron...")

    except Exception as e:
        print(f"⚠ ERROR: {e}")

    finally:
        pa.terminate()
        print("👋 Goodbye!")
        sys.exit(0)



if __name__ == "__main__":
    main()
