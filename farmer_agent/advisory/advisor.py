# Offline Personalized Crop Advisory
import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
CONFIG_DIR = os.path.join(os.path.dirname(__file__), '..', 'config')

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_crop_advice(crop_name, soil_type=None):
    """
    Generate personalized crop advice using local data.
    """
    crops = load_json(os.path.join(CONFIG_DIR, 'crops.json'))
    soil_data = load_json(os.path.join(DATA_DIR, 'soil_data.json'))
    market_prices = load_json(os.path.join(DATA_DIR, 'market_prices.json'))

    crop_info = crops.get(crop_name, {})
    soil_info = soil_data.get(soil_type, {}) if soil_type else {}
    market_info = market_prices.get(crop_name, {})

    advice = []
    advice.append(f"Crop: {crop_name}")
    advice.append(f"Recommended Soil: {crop_info.get('recommended_soil', 'N/A')}")
    advice.append(f"Current Soil: {soil_type if soil_type else 'N/A'}")
    advice.append(f"Soil Notes: {soil_info.get('notes', 'N/A')}")
    advice.append(f"Market Price: {market_info.get('price', 'N/A')}")
    if crop_info.get('climate_smart_tips'):
        advice.append("Climate-Smart Tips:")
        for tip in crop_info['climate_smart_tips']:
            advice.append(f"- {tip}")
    if crop_info.get('care_instructions'):
        advice.append("Care Instructions:")
        for inst in crop_info['care_instructions']:
            advice.append(f"- {inst}")
    return "\n".join(advice)

if __name__ == "__main__":
    # Example usage
    crop = input("Enter crop name: ")
    soil = input("Enter soil type (optional): ")
    result = get_crop_advice(crop, soil if soil else None)
    print(json.dumps(result, indent=2, ensure_ascii=False))
