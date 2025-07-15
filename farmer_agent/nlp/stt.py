# Offline Speech-to-Text using Vosk
import os
import sys
try:
    from vosk import Model, KaldiRecognizer
    import pyaudio
except ImportError:
    print("Please install vosk and pyaudio: pip install vosk pyaudio")
    sys.exit(1)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model")

def recognize_speech(duration=5, lang="en"):
    """
    Records audio from the microphone and returns recognized text (offline).
    """
    if not os.path.exists(MODEL_PATH):
        print(f"Vosk model not found at {MODEL_PATH}. Download and place the model folder here.")
        return ""
    model = Model(MODEL_PATH)
    rec = KaldiRecognizer(model, 16000)
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
    stream.start_stream()
    print("Speak now...")
    result = ""
    for _ in range(int(16000 / 8000 * duration)):
        data = stream.read(4000, exception_on_overflow=False)
        if rec.AcceptWaveform(data):
            res = rec.Result()
            import json
            result = json.loads(res).get('text', '')
            break
    stream.stop_stream()
    stream.close()
    p.terminate()
    return result

if __name__ == "__main__":
    text = recognize_speech()
    print("Recognized:", text)
import whisper

class STT:
    def __init__(self):
        # Make sure openai-whisper is installed: pip install openai-whisper
        import whisper
        self.model = whisper.load_model("base")

    def transcribe_audio(self, file_path: str, language: str = "auto") -> str:
        try:
            result = self.model.transcribe(file_path, language=language)
            text = result["text"]
            if isinstance(text, list):
                text = " ".join(str(t) for t in text)
            return text
        except Exception as e:
            return f"[Error] {str(e)}"