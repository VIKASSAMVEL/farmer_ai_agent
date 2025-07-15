
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
        self._mic_recording_path = None  # Track last mic recording

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

    def record_from_mic(self, output_path=None):
        """
        Starts recording audio from the microphone in a background thread. Keeps recording until stop_recording_from_mic is called.
        Returns None when started.
        """
        import threading
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
        print("Mic recording started. Press the mic button again to stop.")
        self._mic_stream = stream
        self._mic_pyaudio = p
        self._mic_frames = []
        self._mic_recording = True
        def _record():
            while self._mic_recording:
                data = self._mic_stream.read(CHUNK, exception_on_overflow=False)
                self._mic_frames.append(data)
        self._mic_thread = threading.Thread(target=_record, daemon=True)
        self._mic_thread.start()
        return None  # Recording started, no file yet

    # append_mic_frame is no longer needed; recording is handled in a thread

    def stop_recording_from_mic(self, output_path=None):
        """
        Stops mic recording and saves the audio to output_path. Returns the file path.
        """
        if not hasattr(self, '_mic_stream') or not self._mic_recording:
            return "[Error] Mic was not recording."
        self._mic_recording = False
        self._mic_stream.stop_stream()
        self._mic_stream.close()
        self._mic_pyaudio.terminate()
        if not output_path:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            output_path = tmp.name
            tmp.close()
        wf = wave.open(output_path, 'wb')
        wf.setnchannels(1)
        import pyaudio
        wf.setsampwidth(self._mic_pyaudio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(16000)
        wf.writeframes(b''.join(self._mic_frames))
        wf.close()
        return output_path

    def recognize(self, source="file", language: str = "auto", file_path: str = "", toggle=False) -> str:
        """
        Unified interface: source="mic" or "file". If mic, starts/stops recording and transcribes with Whisper.
        """
        if source == "mic":
            if not self._mic_recording_path:
                self.record_from_mic()
                self._mic_recording_path = "[Mic Recording Started]"
                return "[Mic Recording Started]"
            else:
                audio_path = self.stop_recording_from_mic()
                self._mic_recording_path = None
                return self.transcribe_audio(audio_path, language=language)
        elif source == "file" and file_path:
            return self.transcribe_audio(file_path, language=language)
        else:
            return "[Error] Please provide a valid source ('mic' or 'file') and file_path if using file."


def recognize_speech(source="file", lang: str = "auto", whisper_model: str = "base", duration=5, file_path: str = ""):
    """
    Unified function for CLI/UI: uses Whisper for all Indian languages. Supports mic or file.
    """
    stt = STT(whisper_model=whisper_model)
    return stt.recognize(source=source, language=lang, file_path=file_path or "")

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
        print("Recording from mic. Press Ctrl+C to stop and transcribe.")
        stt = STT(whisper_model=args.model)
        try:
            stt.record_from_mic()
            while True:
                pass  # Recording in background thread; wait for KeyboardInterrupt
        except KeyboardInterrupt:
            print("\nStopping recording and transcribing...")
            audio_path = stt.stop_recording_from_mic()
            result = stt.transcribe_audio(audio_path, language=args.lang)
            print("Recognized:", result)
    elif args.file:
        print("Transcribing file with Whisper...")
        print("Recognized:", recognize_speech(source="file", file_path=args.file, lang=args.lang, whisper_model=args.model))
    else:
        print("Please provide either --mic or --file.")