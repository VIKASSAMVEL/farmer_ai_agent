import requests

def call_llm(prompt, model="phi3:mini", host="http://localhost:11434", max_tokens=512, timeout=60):
    """
    Call a local LLM (Ollama) with the given prompt and return the response text.
    """
    url = f"{host}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": max_tokens}
    }
    try:
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        llm_response = response.json().get("response", "").strip()
        return llm_response
    except Exception as e:
        return f"[LLM error: {e}]"
