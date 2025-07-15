# Utility functions for file and data handling (offline)
import json
import os

def load_json(file_path):
    """
    Load JSON data from a file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, file_path):
    """
    Save data as JSON to a file.
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def validate_json(data, required_keys):
    """
    Validate that required keys exist in the JSON data.
    """
    missing = [key for key in required_keys if key not in data]
    return missing
