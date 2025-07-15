# Accessibility Utilities
# Support for larger text, high-contrast mode, and voice navigation

class Accessibility:
    def __init__(self, large_text=False, high_contrast=False, voice_nav=False):
        self.large_text = large_text
        self.high_contrast = high_contrast
        self.voice_nav = voice_nav

    def format_text(self, text):
        if self.large_text:
            return f"\n{'='*40}\n{text.upper()}\n{'='*40}\n"
        return text

    def apply_contrast(self, text):
        if self.high_contrast:
            # Simple simulation: add markers for high contrast
            return f"*** {text} ***"
        return text

    def speak_text(self, text):
        if self.voice_nav:
            try:
                from nlp.tts import speak
                speak(text)
            except Exception:
                print("Voice navigation unavailable.")

if __name__ == "__main__":
    acc = Accessibility(large_text=True, high_contrast=True, voice_nav=False)
    sample = "Welcome to Farmer Agent!"
    print(acc.format_text(sample))
    print(acc.apply_contrast(sample))
    acc.speak_text(sample)
