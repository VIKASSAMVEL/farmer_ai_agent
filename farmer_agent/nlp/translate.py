# Offline Translation for Regional Indian Languages using IndicTrans
import sys
try:
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
except ImportError:
    print("Please install transformers: pip install transformers")
    sys.exit(1)

# Download the model once, then use offline
MODEL_NAME = "ai4bharat/indictrans-v2-all-gpu"

class OfflineTranslator:
    def __init__(self, model_name=MODEL_NAME):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    def translate(self, text, src_lang, tgt_lang):
        """
        Translate text from src_lang to tgt_lang (e.g., 'hi' to 'ta').
        """
        input_text = f"<2{tgt_lang}> {text}"
        inputs = self.tokenizer(input_text, return_tensors="pt")
        outputs = self.model.generate(**inputs)
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

if __name__ == "__main__":
    translator = OfflineTranslator()
    # Example: Hindi to Tamil
    src = "नमस्ते किसान"
    print("Hindi to Tamil:", translator.translate(src, "hi", "ta"))
