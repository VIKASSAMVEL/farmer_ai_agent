# Offline Text-to-Speech for Regional Indian Languages
# To expand language support, install additional Indian voices in Windows settings.
# Use pyttsx3 to list and select voices for Hindi, Tamil, Telugu, Bengali, etc.
import pyttsx3

def speak(text, lang_voice=None):
    """
    Speak the given text using offline TTS. Optionally set a voice for Indian languages.
    """
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    if lang_voice:
        # Try to set the voice by name or language code
        found_voice = False
        if isinstance(voices, (list, tuple)):
            for voice in voices:
                name = getattr(voice, 'name', '').lower()
                vid = getattr(voice, 'id', '').lower()
                if lang_voice.lower() in name or lang_voice.lower() in vid:
                    engine.setProperty('voice', getattr(voice, 'id', ''))
                    found_voice = True
                    break
        else:
            name = getattr(voices, 'name', '').lower()
            vid = getattr(voices, 'id', '').lower()
            if lang_voice.lower() in name or lang_voice.lower() in vid:
                engine.setProperty('voice', getattr(voices, 'id', ''))
                found_voice = True
        if not found_voice:
            print(f"Warning: Voice '{lang_voice}' not found. Using default voice.")
    engine.say(text)
    engine.runAndWait()

def list_voices():
    """
    List all available voices on the system. To add more Indian languages, install them in Windows language settings.
    """
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    # Robustly handle voices property
    if isinstance(voices, (list, tuple)):
        for idx, voice in enumerate(voices):
            name = getattr(voice, 'name', str(voice))
            vid = getattr(voice, 'id', str(voice))
            print(f"Voice {idx}: {name} | ID: {vid}")
    else:
        name = getattr(voices, 'name', str(voices))
        vid = getattr(voices, 'id', str(voices))
        print(f"Voice 0: {name} | ID: {vid}")

if __name__ == "__main__":
    print("Available voices:")
    list_voices()
    # Example usage: speak in Hindi (if installed)
    # speak("नमस्ते किसान", lang_voice="hindi")
