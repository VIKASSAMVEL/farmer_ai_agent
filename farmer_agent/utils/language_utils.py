import re
from farmer_agent.utils.llm_utils import call_llm

# Simple language detection using LLM (fallback to langdetect if available)
def detect_language(text, default='en'):
    try:
        prompt = f"Detect the language code (ISO 639-1) for this text: '{text}'. Only output the code."
        code = call_llm(prompt).strip().lower()
        # Validate code (should be two letters)
        if re.match(r'^[a-z]{2}$', code):
            return code
    except Exception:
        pass
    return default

# LLM-based translation utility
def llm_translate(text, target_lang, source_lang=None):
    prompt = f"Translate the following text to {target_lang}:\n{text}"
    if source_lang:
        prompt = f"Translate the following text from {source_lang} to {target_lang}:\n{text}"
    return call_llm(prompt)
