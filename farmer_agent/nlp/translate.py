
# Offline Translation for Regional Indian Languages using MarianMT
# To expand language support, use MarianMT models from Hugging Face.
# Supported languages: Hindi (hi), Tamil (ta), Telugu (te), Kannada (kn), Malayalam (ml), English (en), and more.
# Example usage: translator.translate(text, src_lang, tgt_lang)

import sys
try:
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
except ImportError:
    print("Please install transformers: pip install transformers")
    sys.exit(1)
try:
    from indictrans import IndicProcessor # type: ignore
except ImportError:
    IndicProcessor = None


# Use MarianMT for Hindi and Malayalam, IndicTrans2 for Tamil, Telugu, Kannada, Malayalam
MARIAN_MODELS = {
    ("en", "hi"): "Helsinki-NLP/opus-mt-en-hi",
    ("hi", "en"): "Helsinki-NLP/opus-mt-hi-en",
    ("en", "ml"): "Helsinki-NLP/opus-mt-en-ml",
    ("ml", "en"): "Helsinki-NLP/opus-mt-ml-en",
}

INDICTRANS2_MODEL = "ai4bharat/indictrans2-en-indic-1B"

# Default to English-Hindi
DEFAULT_MODEL = MARIAN_MODELS[("en", "hi")]




LANG_CODE_MAP = {
    "en": "eng_Latn",
    "hi": "hin_Deva",
    "ta": "tam_Taml",
    "te": "tel_Telu",
    "kn": "kan_Knda",
    "ml": "mal_Mlym",
}

class OfflineTranslator:
    def __init__(self, model_name=None):
        self.model_name = model_name or DEFAULT_MODEL
        self.tokenizer = None
        self.model = None
        self.processor = IndicProcessor(inference=True) if IndicProcessor else None
        self._load_model(self.model_name)

    def _load_model(self, model_name):
        try:
            trust_remote = False
            if model_name == INDICTRANS2_MODEL:
                trust_remote = True
            self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=trust_remote)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name, trust_remote_code=trust_remote)
            self.model_name = model_name
        except Exception as e:
            print(f"[Error] Could not load model '{model_name}': {e}")
            self.tokenizer = None
            self.model = None

    def translate(self, text, src_lang="en", tgt_lang="hi"):
        """
        Translate text from src_lang to tgt_lang. Uses MarianMT for Hindi/Malayalam, IndicTrans2 for Tamil, Telugu, Kannada, Malayalam.
        """
        indic_langs = {"ta", "te", "kn", "ml"}
        if (src_lang in indic_langs or tgt_lang in indic_langs) and not ((src_lang, tgt_lang) in MARIAN_MODELS):
            # Use IndicTrans2 for these pairs
            if self.model_name != INDICTRANS2_MODEL:
                self._load_model(INDICTRANS2_MODEL)
            if not self.tokenizer or not self.model or not self.processor:
                return "[Error] Translation model or processor not loaded."
            try:
                src_code = LANG_CODE_MAP.get(src_lang, src_lang)
                tgt_code = LANG_CODE_MAP.get(tgt_lang, tgt_lang)
                batch = self.processor.preprocess_batch([text], src_lang=src_code, tgt_lang=tgt_code)
                inputs = self.tokenizer(
                    batch,
                    truncation=True,
                    padding="longest",
                    return_tensors="pt",
                    return_attention_mask=True,
                )
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self.model = self.model.to(device)
                inputs = {k: v.to(device) for k, v in inputs.items()}
                with torch.no_grad():
                    generated_tokens = self.model.generate(
                        **inputs,
                        use_cache=True,
                        min_length=0,
                        max_length=256,
                        num_beams=5,
                        num_return_sequences=1,
                    )
                generated_tokens = self.tokenizer.batch_decode(
                    generated_tokens,
                    skip_special_tokens=True,
                    clean_up_tokenization_spaces=True,
                )
                translations = self.processor.postprocess_batch(generated_tokens, lang=tgt_code)
                return translations[0]
            except Exception as e:
                return f"[Error] Translation failed: {e}"
        else:
            # Use MarianMT for Hindi/Malayalam
            model_key = (src_lang, tgt_lang)
            model_name = MARIAN_MODELS.get(model_key)
            if not model_name:
                return f"[Error] No model for {src_lang} to {tgt_lang}."
            if self.model_name != model_name:
                self._load_model(model_name)
            if not self.tokenizer or not self.model:
                return "[Error] Translation model not loaded."
            try:
                inputs = self.tokenizer(text, return_tensors="pt")
                outputs = self.model.generate(**inputs)
                return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            except Exception as e:
                return f"[Error] Translation failed: {e}"

    def supported_languages(self):
        # All supported language codes
        return ["en", "hi", "ta", "te", "kn", "ml"]



if __name__ == "__main__":
    print("OfflineTranslator demo (MarianMT + IndicTrans2)")
    translator = OfflineTranslator()
    print("Supported languages:", translator.supported_languages())
    src = "Hello farmer"
    print("English to Hindi:", translator.translate(src, "en", "hi"))
    print("English to Tamil:", translator.translate(src, "en", "ta"))
    print("English to Telugu:", translator.translate(src, "en", "te"))
    print("English to Kannada:", translator.translate(src, "en", "kn"))
    print("English to Malayalam:", translator.translate(src, "en", "ml"))
