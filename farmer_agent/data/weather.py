# Offline Weather Estimation
# Provides basic weather advice using preloaded patterns or simple algorithms
import json
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
WEATHER_FILE = os.path.join(DATA_DIR, 'weather_patterns.json')

class WeatherEstimator:
    def __init__(self):
        self.patterns = self.load_patterns()

    def load_patterns(self):
        if not os.path.exists(WEATHER_FILE):
            # Default patterns for demonstration
            return {
                "summer": {"temperature": 35, "humidity": 40, "advice": "Irrigate crops frequently."},
                "monsoon": {"temperature": 28, "humidity": 80, "advice": "Monitor for fungal diseases."},
                "winter": {"temperature": 18, "humidity": 50, "advice": "Protect crops from frost."}
            }
        with open(WEATHER_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    def estimate(self, season=None):
        if not season:
            month = datetime.now().month
            if month in [3,4,5,6]:
                season = "summer"
            elif month in [7,8,9,10]:
                season = "monsoon"
            else:
                season = "winter"
        return self.patterns.get(season, {})

if __name__ == "__main__":
    estimator = WeatherEstimator()
    print("Estimated weather for current season:", estimator.estimate())
    print("Estimated weather for 'monsoon':", estimator.estimate('monsoon'))
