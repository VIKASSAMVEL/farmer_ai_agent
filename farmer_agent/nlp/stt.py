
# Unified Speech-to-Text: Vosk (offline, mic) and Whisper (file, multi-language)
import os
import sys

class STT:
    def __init__(self, engine="vosk", model_path=None, whisper_model="base"):
        self.engine = engine
        self.model_path = model_path or os.path.join(os.path.dirname(__file__), "model")
        self.whisper_model = whisper_model
        self._vosk_model = None
        self._whisper_model = None

    def recognize_speech(self, duration=5, lang="en"):
        """
        Records audio from the microphone and returns recognized text (offline, Vosk).
        """
        try:
            from vosk import Model, KaldiRecognizer
            import pyaudio
        except ImportError:
            print("Please install vosk and pyaudio: pip install vosk pyaudio")
            return ""
        if not os.path.exists(self.model_path):
            print(f"Vosk model not found at {self.model_path}. Download and place the model folder here.")
            return ""
        if not self._vosk_model:
            self._vosk_model = Model(self.model_path)
        rec = KaldiRecognizer(self._vosk_model, 16000)
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
        stream.start_stream()
        print("Speak now...")
        result = ""
        for _ in range(int(16000 / 8000 * duration)):
            data = stream.read(4000, exception_on_overflow=False)
            if rec.AcceptWaveform(data):
                import json
                res = rec.Result()
                result = json.loads(res).get('text', '')
                break
        stream.stop_stream()
        stream.close()
        p.terminate()
        return result

    def transcribe_audio(self, file_path: str, language: str = "auto") -> str:
        """
        Transcribe an audio file using Whisper (multi-language, file-based).
        """
        try:
            import whisper
        except ImportError:
            return "[Error] Please install openai-whisper: pip install openai-whisper"
        if not self._whisper_model:
            self._whisper_model = whisper.load_model(self.whisper_model)
        try:
            result = self._whisper_model.transcribe(file_path, language=language)
            text = result["text"]
            if isinstance(text, list):
                text = " ".join(str(t) for t in text)
            return text
        except Exception as e:
            return f"[Error] {str(e)}"

    def recognize(self, source="mic", **kwargs):
        """
        Unified interface: source="mic" (vosk) or source="file" (whisper)
        """
        if source == "mic":
            return self.recognize_speech(**kwargs)
        elif source == "file":
            return self.transcribe_audio(kwargs.get("file_path", ""), language=kwargs.get("language", "auto"))
        else:
            return "[Error] Unknown source. Use 'mic' or 'file'."

def recognize_speech(duration=5, lang="en", engine="vosk", file_path=None):
    """
    Unified function for CLI/UI: use Vosk for mic, Whisper for file.
    """
    stt = STT(engine=engine)
    if file_path:
        return stt.transcribe_audio(file_path, language=lang)
    else:
        return stt.recognize_speech(duration=duration, lang=lang)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Speech-to-Text Demo (Vosk/Whisper)")
    parser.add_argument('--file', type=str, help='Audio file to transcribe (uses Whisper)')
    parser.add_argument('--lang', type=str, default='en', help='Language code (default: en)')
    parser.add_argument('--duration', type=int, default=5, help='Mic record duration (seconds, Vosk)')
    args = parser.parse_args()
    if args.file:
        print("Transcribing file with Whisper...")
        print("Recognized:", recognize_speech(file_path=args.file, lang=args.lang, engine="whisper"))
    else:
        print("Recording from mic with Vosk...")
        print("Recognized:", recognize_speech(duration=args.duration, lang=args.lang, engine="vosk"))