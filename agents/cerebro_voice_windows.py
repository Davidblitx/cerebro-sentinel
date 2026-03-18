import speech_recognition as sr
import pyttsx3
import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "cerebro-v1"

CEREBRO_IDENTITY = """You are CEREBRO Sentinel v0.1. You serve only David. Be concise, intelligent and direct. Max 3 sentences per response."""

engine = pyttsx3.init()
engine.setProperty("rate", 165)

def speak(text):
    print(f"\n[CEREBRO] {text}\n")
    engine.say(text)
    engine.runAndWait()

def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("[CEREBRO] Listening...")
        r.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = r.listen(source, timeout=8, phrase_time_limit=15)
            text = r.recognize_google(audio)
            print(f"David: {text}")
            return text
        except:
            return ""

def think(text, history):
    history.append({"role": "user", "content": text})
    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": CEREBRO_IDENTITY}] + history,
        "stream": False
    }
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=60)
        reply = r.json()["message"]["content"]
        history.append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        return f"Connection error: {e}"

history = []
print("=" * 50)
print("  CEREBRO Sentinel v0.4 - Voice Interface")
print("=" * 50)
speak("Good morning David. CEREBRO Sentinel is online.")

while True:
    try:
        user_input = listen()
        if not user_input:
            continue
        if any(w in user_input.lower() for w in ["goodbye", "exit", "stop"]):
            speak("Goodbye David.")
            break
        print("[CEREBRO] Thinking...")
        response = think(user_input, history)
        speak(response)
    except KeyboardInterrupt:
        speak("Goodbye David.")
        break
