
# Unified Speech-to-Text: Vosk (offline, mic) and Whisper (file, multi-language)
import os
import sys


# Whisper-only STT for all Indian regional languages
import tempfile
import wave

class STT:
    def __init__(self, whisper_model="base"):
        """
        Whisper model name ("base", "small", "medium", "large", etc.).
        Whisper supports all major Indian languages (see https://github.com/openai/whisper#available-models-and-languages).
        """
        self.whisper_model = whisper_model
        self._whisper_model = None

    def transcribe_audio(self, file_path: str, language: str = "auto") -> str:
        """
        Transcribe an audio file using Whisper (multi-language, file-based).
        For Indian languages, set language to ISO code (e.g., 'hi', 'ta', 'te', 'kn', 'ml', etc.).
        """
        try:
            import whisper
        except ImportError:
            return "[Error] Please install openai-whisper: pip install openai-whisper"
        if not file_path:
            return "[Error] No audio file provided."
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

    def record_from_mic(self, duration=5, output_path=None):
        """
        Records audio from the microphone and saves to output_path (WAV, 16kHz mono). Returns the file path.
        """
        try:
            import pyaudio
        except ImportError:
            return "[Error] Please install pyaudio: pip install pyaudio"
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        print(f"Recording from mic for {duration} seconds...")
        frames = []
        for _ in range(0, int(RATE / CHUNK * duration)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
        stream.stop_stream()
        stream.close()
        p.terminate()
        if not output_path:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            output_path = tmp.name
            tmp.close()
        wf = wave.open(output_path, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        return output_path

    def recognize(self, source="file", language: str = "auto", duration=5, file_path: str = "") -> str:
        """
        Unified interface: source="mic" or "file". If mic, records then transcribes with Whisper.
        """
        if source == "mic":
            audio_path = self.record_from_mic(duration=duration)
            if isinstance(audio_path, str) and audio_path.endswith('.wav'):
                return self.transcribe_audio(audio_path, language=language)
            else:
                return audio_path if isinstance(audio_path, str) else "[Error] Mic recording failed."
        elif source == "file" and file_path:
            return self.transcribe_audio(file_path, language=language)
        else:
            return "[Error] Please provide a valid source ('mic' or 'file') and file_path if using file."


def recognize_speech(source="file", lang: str = "auto", whisper_model: str = "base", duration=5, file_path: str = ""):
    """
    Unified function for CLI/UI: uses Whisper for all Indian languages. Supports mic or file.
    """
    stt = STT(whisper_model=whisper_model)
    return stt.recognize(source=source, language=lang, duration=duration, file_path=file_path or "")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Speech-to-Text Demo (Whisper only, all Indian languages)")
    parser.add_argument('--file', type=str, help='Audio file to transcribe (if not using mic)')
    parser.add_argument('--lang', type=str, default='auto', help='Language code (default: auto)')
    parser.add_argument('--model', type=str, default='base', help='Whisper model (base/small/medium/large)')
    parser.add_argument('--mic', action='store_true', help='Record from mic instead of file')
    parser.add_argument('--duration', type=int, default=5, help='Mic record duration (seconds)')
    args = parser.parse_args()
    if args.mic:
        print("Recording from mic and transcribing with Whisper...")
        print("Recognized:", recognize_speech(source="mic", lang=args.lang, whisper_model=args.model, duration=args.duration))
    elif args.file:
        print("Transcribing file with Whisper...")
        print("Recognized:", recognize_speech(source="file", file_path=args.file, lang=args.lang, whisper_model=args.model))
    else:
        print("Please provide either --mic or --file.")