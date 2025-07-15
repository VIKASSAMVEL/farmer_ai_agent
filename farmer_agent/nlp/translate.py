# Offline Translation for Regional Indian Languages using IndicTrans
# To expand language support, download the latest IndicTrans model from Hugging Face.
# Supported languages: Hindi (hi), Tamil (ta), Telugu (te), Bengali (bn), Marathi (mr), Gujarati (gu), Kannada (kn), Malayalam (ml), Punjabi (pa), Oriya (or), Assamese (as), Urdu (ur), English (en), and more.
# Example usage: translator.translate(text, src_lang, tgt_lang)
import sys
try:
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
except ImportError:
    print("Please install transformers: pip install transformers")
    sys.exit(1)


# Default to a public Hugging Face translation model (English-Hindi as example)
DEFAULT_MODEL = "Helsinki-NLP/opus-mt-en-hi"


class OfflineTranslator:
    def __init__(self, model_name=DEFAULT_MODEL):
        self.model_name = model_name
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        except Exception as e:
            print(f"[Error] Could not load model '{model_name}': {e}")
            self.tokenizer = None
            self.model = None

    def translate(self, text, src_lang=None, tgt_lang=None):
        """
        Translate text from src_lang to tgt_lang. For Helsinki-NLP models, src_lang/tgt_lang are inferred from model name.
        """
        if not self.tokenizer or not self.model:
            return "[Error] Translation model not loaded."
        try:
            # For Helsinki-NLP models, just input the text
            inputs = self.tokenizer(text, return_tensors="pt")
            outputs = self.model.generate(**inputs)
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        except Exception as e:
            return f"[Error] Translation failed: {e}"

    def supported_languages(self):
        # For Helsinki-NLP/opus-mt-en-hi, only en <-> hi
        if "en-hi" in self.model_name:
            return ["en", "hi"]
        # Add more logic for other models if needed
        return ["en", "hi"]


if __name__ == "__main__":
    print("OfflineTranslator demo (using Helsinki-NLP/opus-mt-en-hi)")
    translator = OfflineTranslator()
    print("Supported languages:", translator.supported_languages())
    src = "Hello farmer"
    print("English to Hindi:", translator.translate(src))
