# Offline Text-to-Speech for Regional Indian Languages
import pyttsx3

def speak(text, lang_voice=None):
    """
    Speak the given text using offline TTS. Optionally set a voice for Indian languages.
    """
    engine = pyttsx3.init()
    # List available voices
    voices = engine.getProperty('voices')
    if lang_voice:
        # Try to set the voice by name or language code
        for voice in voices:
            if lang_voice.lower() in voice.name.lower() or lang_voice.lower() in voice.id.lower():
                engine.setProperty('voice', voice.id)
                break
    engine.say(text)
    engine.runAndWait()

def list_voices():
    """
    List all available voices on the system.
    """
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    for idx, voice in enumerate(voices):
        print(f"Voice {idx}: {voice.name} | ID: {voice.id}")

if __name__ == "__main__":
    print("Available voices:")
    list_voices()
    # Example usage: speak in Hindi (if installed)
    # speak("नमस्ते किसान", lang_voice="hindi")
