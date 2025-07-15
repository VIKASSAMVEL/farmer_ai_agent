

# PlantIdentifier class for agentic/LLM integration
from inference_sdk import InferenceHTTPClient

class PlantIdentifier:
    def get_llm_disease_tips(self, disease_summary, model="llama3:8b", host="http://localhost:11434"):
        """
        Use local LLM (Ollama) to provide tips, solutions, and medicine recommendations based on detected disease(s).
        disease_summary: string output from identify()
        Returns a string of advice/tips.
        """
        if not disease_summary or disease_summary == "No disease detected.":
            return "No disease detected. No tips needed."
        try:
            import requests
            prompt = (
                "You are an expert plant pathologist. Based on the following detected plant diseases, provide actionable tips, recommended solutions, and suitable medicines for Indian farmers. "
                "Be concise and practical.\n"
                f"Detected diseases: {disease_summary}\n"
                "Tips, Solutions, Medicines:"
            )
            url = f"{host}/api/generate"
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            llm_response = response.json().get("response", "")
            return llm_response.strip()
        except Exception as e:
            return f"[LLM error: {e}]"
    def __init__(self, api_key=None):
        self.client = InferenceHTTPClient(
            api_url="https://serverless.roboflow.com",
            api_key=api_key or "HAISJzXtj7t48iPVJhQG"
        )

    def identify(self, image_path, model_id="leaf-disease-f06v7/1"):
        result = self.client.infer(image_path, model_id=model_id)
        # Summarize result for LLM prompt
        preds = []
        if isinstance(result, dict) and 'predictions' in result:
            preds = result['predictions']
        elif isinstance(result, list):
            preds = result
        if not preds:
            return "No disease detected."
        summary = []
        for pred in preds:
            summary.append(f"Detected: {pred['class']} (confidence: {pred['confidence']:.2f})")
        return "\n".join(summary)