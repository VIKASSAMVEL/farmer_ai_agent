# Offline Weather Estimation
# Provides basic weather advice using preloaded patterns or simple algorithms
import json
import os
import requests
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
WEATHER_FILE = os.path.join(DATA_DIR, 'weather_patterns.json')

class WeatherEstimator:
    def get_current_location(self):
        """
        Get current location (city) using IP geolocation API (ipinfo.io).
        Returns city name or None if not available.
        """
        try:
            resp = requests.get("https://ipinfo.io/json", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("city")
        except Exception as e:
            print(f"IP geolocation error: {e}")
        return None
    def __init__(self, api_key=None, openweather_api_key=None):
        self.patterns = self.load_patterns()
        self.default = {
            "temperature": 30,
            "humidity": 50,
            "rainfall": 0,
            "wind": "Calm",
            "advice": "Monitor local conditions.",
            "warnings": []
        }
        self.api_key = api_key or os.environ.get('WEATHERAPI_KEY')
        self.openweather_api_key = openweather_api_key or os.environ.get('OPENWEATHER_API_KEY')
    def fetch_openweather(self, location):
        """
        Fetch real weather data from OpenWeatherMap (https://openweathermap.org/api)
        Returns a dict with temperature, humidity, rainfall, wind, etc.
        """
        if not self.openweather_api_key or not location:
            return None
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={self.openweather_api_key}&units=metric"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                main = data.get('main', {})
                wind = data.get('wind', {})
                rain = data.get('rain', {})
                weather_desc = data.get('weather', [{}])[0].get('description', '')
                return {
                    "temperature": main.get('temp'),
                    "humidity": main.get('humidity'),
                    "rainfall": rain.get('1h', 0),
                    "wind": f"{wind.get('speed', 'N/A')} m/s {wind.get('deg', '')}",
                    "advice": f"{weather_desc.capitalize()}. Monitor local weather conditions.",
                    "warnings": []
                }
        except Exception as e:
            print(f"OpenWeatherMap error: {e}")
        return None
    def fetch_online_weather(self, location):
        """
        Fetch real weather data from WeatherAPI (https://www.weatherapi.com/)
        Returns a dict with temperature, humidity, rainfall, wind, etc.
        """
        if not self.api_key or not location:
            return None
        try:
            url = f"http://api.weatherapi.com/v1/current.json?key={self.api_key}&q={location}"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                current = data.get('current', {})
                return {
                    "temperature": current.get('temp_c'),
                    "humidity": current.get('humidity'),
                    "rainfall": current.get('precip_mm'),
                    "wind": f"{current.get('wind_kph', 'N/A')} kph {current.get('wind_dir', '')}",
                    "advice": "Monitor local weather conditions.",
                    "warnings": []
                }
        except Exception as e:
            print(f"WeatherAPI error: {e}")
        return None

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

    def estimate(self, season=None, location=None, crop=None, date=None, use_online=True, prefer_openweather=True):
        """
        Estimate weather for a given season, location, crop, or date.
        - season: 'summer', 'monsoon', 'winter', etc.
        - location: string (optional, for future expansion)
        - crop: string (optional, gives crop-specific advice)
        - date: datetime/date (optional, for daily forecast)
        - use_online: bool, if True and API key is set, try to fetch real data
        """
        # Try OpenWeatherMap first if enabled and preferred
        if use_online and self.openweather_api_key and location and prefer_openweather:
            online = self.fetch_openweather(location)
            if online:
                pattern = online.copy()
                if crop:
                    if crop.lower() in ["rice", "paddy"]:
                        pattern["advice"] += " Rice grows well in wet conditions, but ensure proper drainage."
                    elif crop.lower() in ["wheat"]:
                        pattern["advice"] += " Wheat is sensitive to frost; cover seedlings if needed."
                    elif crop.lower() in ["tomato"]:
                        pattern["advice"] += " Provide shade to tomato plants during peak heat."
                return pattern
        # Try WeatherAPI if enabled and not preferring OpenWeatherMap
        if use_online and self.api_key and location:
            online = self.fetch_online_weather(location)
            if online:
                pattern = online.copy()
                if crop:
                    if crop.lower() in ["rice", "paddy"]:
                        pattern["advice"] += " Rice grows well in wet conditions, but ensure proper drainage."
                    elif crop.lower() in ["wheat"]:
                        pattern["advice"] += " Wheat is sensitive to frost; cover seedlings if needed."
                    elif crop.lower() in ["tomato"]:
                        pattern["advice"] += " Provide shade to tomato plants during peak heat."
                return pattern
        # Fallback to offline
        if not season:
            month = (date.month if date else datetime.now().month)
            if month in [3,4,5,6]:
                season = "summer"
            elif month in [7,8,9,10]:
                season = "monsoon"
            else:
                season = "winter"
        pattern = self.patterns.get(season, self.default.copy())
        if crop:
            pattern = pattern.copy()
            if crop.lower() in ["rice", "paddy"] and season == "monsoon":
                pattern["advice"] += " Rice grows well in monsoon, but ensure proper drainage."
            elif crop.lower() in ["wheat"] and season == "winter":
                pattern["advice"] += " Wheat is sensitive to frost; cover seedlings if needed."
            elif crop.lower() in ["tomato"] and season == "summer":
                pattern["advice"] += " Provide shade to tomato plants during peak heat."
        if location:
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
    location = estimator.get_current_location()
    if location:
        print(f"Detected location: {location}")
        weather = estimator.estimate(location=location, use_online=True)
        print(f"Weather for {location}:")
        print(json.dumps(weather, indent=2, ensure_ascii=False))
    else:
        print("Could not detect location. Showing default weather estimate.")
        print("Estimated weather for current season:", estimator.estimate())
