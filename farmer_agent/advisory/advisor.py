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

    advice = {
        'crop': crop_name,
        'recommended_soil': crop_info.get('recommended_soil', 'N/A'),
        'current_soil': soil_type,
        'soil_notes': soil_info.get('notes', 'N/A'),
        'market_price': market_info.get('price', 'N/A'),
        'climate_smart_tips': crop_info.get('climate_smart_tips', []),
        'care_instructions': crop_info.get('care_instructions', []),
    }
    return advice

if __name__ == "__main__":
    # Example usage
    crop = input("Enter crop name: ")
    soil = input("Enter soil type (optional): ")
    result = get_crop_advice(crop, soil if soil else None)
    print(json.dumps(result, indent=2, ensure_ascii=False))
