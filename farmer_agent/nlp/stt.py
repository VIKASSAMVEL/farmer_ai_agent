import whisper

class STT:
    def __init__(self):
        self.model = whisper.load_model("small")

    def transcribe_audio(self, file_path: str, language: str = "auto") -> str:
        try:
            result = self.model.transcribe(file_path, language=language)
            return result["text"]
        except Exception as e:
            return f"[Error] {str(e)}"