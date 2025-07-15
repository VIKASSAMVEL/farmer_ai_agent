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

    # Case-insensitive crop lookup
    crop_key = next((k for k in crops if k.lower() == crop_name.lower()), None) if crop_name else None
    crop_info = crops.get(crop_key, {}) if crop_key else {}

    # Case-insensitive soil lookup
    soil_key = next((k for k in soil_data if k.lower() == soil_type.lower()), None) if soil_type else None
    soil_info = soil_data.get(soil_key, {}) if soil_key else {}

    # Case-insensitive market price lookup
    market_key = next((k for k in market_prices if k.lower() == crop_name.lower()), None) if crop_name else None
    market_info = market_prices.get(market_key, {}) if market_key else {}

    advice = {
        "crop": crop_key if crop_key else crop_name,
        "recommended_soil": crop_info.get('recommended_soil', 'N/A'),
        "current_soil": soil_key if soil_key else (soil_type if soil_type else 'N/A'),
        "soil_notes": soil_info.get('notes', 'N/A'),
        "market_price": market_info.get('price', 'N/A'),
        "climate_smart_tips": crop_info.get('climate_smart_tips', []),
        "care_instructions": crop_info.get('care_instructions', []),
    }

    # Also return a formatted string for CLI/print
    lines = [
        f"Crop: {advice['crop']}",
        f"Recommended Soil: {advice['recommended_soil']}",
        f"Current Soil: {advice['current_soil']}",
        f"Soil Notes: {advice['soil_notes']}",
        f"Market Price: {advice['market_price']}"
    ]
    if advice['climate_smart_tips']:
        lines.append("Climate-Smart Tips:")
        for tip in advice['climate_smart_tips']:
            lines.append(f"- {tip}")
    if advice['care_instructions']:
        lines.append("Care Instructions:")
        for inst in advice['care_instructions']:
            lines.append(f"- {inst}")
    advice['formatted'] = "\n".join(lines)
    return advice

if __name__ == "__main__":
    # Example usage
    crop = input("Enter crop name: ")
    soil = input("Enter soil type (optional): ")
    result = get_crop_advice(crop, soil if soil else None)
    print("\n=== STRUCTURED ADVICE ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("\n=== FORMATTED ADVICE ===")
    print(result['formatted'])
