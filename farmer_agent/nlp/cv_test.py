from inference_sdk import InferenceHTTPClient

CLIENT = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key="HAISJzXtj7t48iPVJhQG"
)

result = CLIENT.infer("E:\\farmer_ai_agent\\farmer_agent\\nlp\\WhatsApp Image 2025-07-15 at 18.45.08_43ff8ecb.jpg", model_id="leaf-disease-f06v7/1")
print(result)