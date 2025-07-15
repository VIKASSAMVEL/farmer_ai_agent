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
        self.default = {
            "temperature": 30,
            "humidity": 50,
            "rainfall": 0,
            "wind": "Calm",
            "advice": "Monitor local conditions.",
            "warnings": []
        }

    def load_patterns(self):
        if not os.path.exists(WEATHER_FILE):
            # Default patterns for demonstration
            return {
                "summer": {"temperature": 35, "humidity": 40, "rainfall": 10, "wind": "Light breeze", "advice": "Irrigate crops frequently.", "warnings": ["Heat stress possible"]},
                "monsoon": {"temperature": 28, "humidity": 80, "rainfall": 200, "wind": "Gusty", "advice": "Monitor for fungal diseases.", "warnings": ["Waterlogging risk"]},
                "winter": {"temperature": 18, "humidity": 50, "rainfall": 5, "wind": "Chilly", "advice": "Protect crops from frost.", "warnings": ["Frost risk"]}
            }
        with open(WEATHER_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    def estimate(self, season=None, location=None, crop=None, date=None):
        """
        Estimate weather for a given season, location, crop, or date.
        - season: 'summer', 'monsoon', 'winter', etc.
        - location: string (optional, for future expansion)
        - crop: string (optional, gives crop-specific advice)
        - date: datetime/date (optional, for daily forecast)
        """
        # Determine season if not provided
        if not season:
            month = (date.month if date else datetime.now().month)
            if month in [3,4,5,6]:
                season = "summer"
            elif month in [7,8,9,10]:
                season = "monsoon"
            else:
                season = "winter"
        # Try to get pattern for season
        pattern = self.patterns.get(season, self.default.copy())
        # Add location/crop-specific advice
        if crop:
            pattern = pattern.copy()
            if crop.lower() in ["rice", "paddy"] and season == "monsoon":
                pattern["advice"] += " Rice grows well in monsoon, but ensure proper drainage."
            elif crop.lower() in ["wheat"] and season == "winter":
                pattern["advice"] += " Wheat is sensitive to frost; cover seedlings if needed."
            elif crop.lower() in ["tomato"] and season == "summer":
                pattern["advice"] += " Provide shade to tomato plants during peak heat."
        if location:
            # For future: location-based microclimate
            pattern = pattern.copy()
            pattern["advice"] += f" (Location: {location})"
        return pattern

    def daily_forecast(self, date=None, location=None):
        """
        Returns a simple daily forecast for a given date/location.
        """
        # For now, just use season logic
        return self.estimate(date=date, location=location)

if __name__ == "__main__":
    estimator = WeatherEstimator()
    print("Estimated weather for current season:", estimator.estimate())
    print("Estimated weather for 'monsoon':", estimator.estimate('monsoon'))
