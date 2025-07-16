import os
import json
import requests
from datetime import datetime

# Paths for data files
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
ENV_LOCAL_PATH = os.path.join(PROJECT_ROOT, 'env.local')
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
WEATHER_FILE = os.path.join(DATA_DIR, 'weather_patterns.json')

# Load environment variables
if os.path.exists(ENV_LOCAL_PATH):
    with open(ENV_LOCAL_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key] = value.strip()

class WeatherEstimator:
    def __init__(self, openweather_api_key=None):
        """Initialize with OpenWeatherMap API key and load offline patterns."""
        self.openweather_api_key = openweather_api_key or os.environ.get('OPENWEATHER_API_KEY')
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
        """Load offline weather patterns from JSON or return defaults."""
        if not os.path.exists(WEATHER_FILE):
            return {
                "summer": {"temperature": 35, "humidity": 40, "rainfall": 10, "wind": "Light breeze", "advice": "Irrigate crops frequently.", "warnings": ["Heat stress possible"]},
                "monsoon": {"temperature": 28, "humidity": 80, "rainfall": 200, "wind": "Gusty", "advice": "Monitor for fungal diseases.", "warnings": ["Waterlogging risk"]},
                "winter": {"temperature": 18, "humidity": 50, "rainfall": 5, "wind": "Chilly", "advice": "Protect crops from frost.", "warnings": ["Frost risk"]}
            }
        with open(WEATHER_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_current_location(self):
        """Get city name using IP geolocation (ipinfo.io)."""
        try:
            resp = requests.get("https://ipinfo.io/json", timeout=5)
            resp.raise_for_status()
            return resp.json().get("city")
        except Exception as e:
            print(f"IP geolocation error: {e}")
            return None

    def fetch_openweather(self, location):
        """Fetch current weather data from OpenWeatherMap and format output cleanly."""
        if not self.openweather_api_key or not location:
            return None
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={self.openweather_api_key}&units=metric"
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            main = data.get('main', {})
            wind = data.get('wind', {})
            rain = data.get('rain', {})
            weather_desc = data.get('weather', [{}])[0].get('description', '')
            # Format output as clean text
            output = (
                f"Temperature: {main.get('temp', 'N/A')}°C\n"
                f"Humidity: {main.get('humidity', 'N/A')}%\n"
                f"Rainfall (last 1h): {rain.get('1h', 0)} mm\n"
                f"Wind: {wind.get('speed', 'N/A')} m/s {wind.get('deg', '')}\n"
                f"Condition: {weather_desc.capitalize()}\n"
                f"Advice: Monitor local weather conditions."
            )
            return output
        except Exception as e:
            print(f"OpenWeatherMap error: {e}")
            return None


    def get_llm_weather_tips(self, weather_data, crop=None, model="llama3:8b", host="http://localhost:11434"):
        """Generate farming tips using local Llama3:8b model based on weather data. Output clean text only."""
        if not weather_data:
            return "No weather data available for tips."
        try:
            # Prepare prompt with weather data and optional crop
            prompt = (
                "You are an agricultural expert for farmers in India. Based on the following weather data, provide practical farming tips "
                "focusing on irrigation, disease prevention, crop protection, and weather-related risks. "
                "Keep the response concise, under 200 words, and formatted as a list with actionable advice."
            )
            if crop:
                prompt += f"\nCrop: {crop}"
            # Use plain text for weather data
            if isinstance(weather_data, str):
                weather_info = weather_data
            elif isinstance(weather_data, dict):
                weather_info = '\n'.join([f"{k.capitalize()}: {v}" for k, v in weather_data.items() if k != 'warnings'])
            else:
                weather_info = str(weather_data)
            prompt += f"\nWeather Data: {weather_info}\nTips:"
            # Call local Llama3:8b via Ollama
            url = f"{host}/api/generate"
            payload = {"model": model, "prompt": prompt, "stream": False}
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            llm_response = response.json().get("response", "").strip()
            # Remove asterisks, quotes, and extra symbols from LLM output
            import re
            clean_response = re.sub(r'["\*\[\]\{\}]', '', llm_response)
            clean_response = re.sub(r'\s*\n\s*', '\n', clean_response)
            return clean_response or "No tips generated."
        except Exception as e:
            return f"LLM error: {e}"

    def estimate(self, season=None, location=None, crop=None, date=None, use_online=True):
        """Estimate weather for a given season, location, crop, or date."""
        # Try online data first if enabled
        if use_online and self.openweather_api_key and location:
            forecast = self.fetch_openweather(location)
            if forecast:
                # If forecast is a dict, copy and add crop advice; if string, just append advice
                if isinstance(forecast, dict):
                    pattern = forecast.copy()
                    if crop:
                        if crop.lower() in ["rice", "paddy"]:
                            pattern["advice"] += " Rice grows well in wet conditions, but ensure proper drainage."
                        elif crop.lower() in ["wheat"]:
                            pattern["advice"] += " Wheat is sensitive to frost; cover seedlings if needed."
                        elif crop.lower() in ["tomato"]:
                            pattern["advice"] += " Provide shade to tomato plants during peak heat."
                    return pattern
                elif isinstance(forecast, str):
                    advice = ""
                    if crop:
                        if crop.lower() in ["rice", "paddy"]:
                            advice = " Rice grows well in wet conditions, but ensure proper drainage."
                        elif crop.lower() in ["wheat"]:
                            advice = " Wheat is sensitive to frost; cover seedlings if needed."
                        elif crop.lower() in ["tomato"]:
                            advice = " Provide shade to tomato plants during peak heat."
                    return forecast + ("\n" + advice if advice else "")
                else:
                    return forecast

        # Fallback to offline patterns
        if not season:
            month = date.month if date else datetime.now().month
            season = "summer" if month in [3, 4, 5, 6] else "monsoon" if month in [7, 8, 9, 10] else "winter"
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
        """Return a daily forecast for a given date/location."""
        return self.estimate(date=date, location=location)

if __name__ == "__main__":
    estimator = WeatherEstimator()
    location = estimator.get_current_location()
    if location:
        print(f"Detected location: {location}")
        current_weather = estimator.fetch_openweather(location)
        if current_weather:
            print(f"Current Weather for {location}:")
            print(json.dumps(current_weather, indent=2, ensure_ascii=False))
            print("\nFarming Tips:")
            print(estimator.get_llm_weather_tips(current_weather))
        else:
            print("Could not fetch weather data. Check API key or location.")
    else:
        print("Could not detect location.")