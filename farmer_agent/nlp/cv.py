

# PlantIdentifier class for agentic/LLM integration
from inference_sdk import InferenceHTTPClient

class PlantIdentifier:
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