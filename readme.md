# Farmer Agent


The Farmer Agent is an AI-powered tool designed to provide tailored agricultural support to small-scale farmers and non-farmers across the world. It leverages natural language processing (NLP), computer vision, and real-time data integration to offer personalized guidance in various languages and mediums. The system now features a modern Kivy-based UI and a CLI, both with full feature parity.

## Key Features


1. **Voice, Text, and Image Input:** Easy communication through voice commands (with automatic language detection), text inputs, or image uploads. The UI features a mic button for speech-to-text: press to start recording, press again to stop and transcribe.
2. **Multilingual NLP & Speech-to-Text:** Understands and responds in regional languages and dialects. Speech-to-text is powered by Whisper (OpenAI), supporting all major Indian languages and automatic language detection from audio (no manual language selection needed).
3. **Plant Identification via Computer Vision:** Detects plant species and diseases using image input.
4. **Personalized Crop Advisory:** Integrates soil, weather, and market data to give tailored advice.
5. **Climate-Smart Recommendations:** Encourages sustainable practices and water-saving techniques.
6. **Offline Mode:** Basic features function without internet access (e.g., image diagnosis, preloaded guidance).
7. **Advanced Crop Calendar & Reminders:**
   - View crop schedules, list all crops, and get next scheduled activity for any crop.
   - Add one-time or recurring reminders for any crop activity.
   - Delete reminders by crop, activity, or date.
   - All calendar/reminder features available in both CLI and UI.

# Farmer AI Agent

## Overview
Farmer AI Agent is an offline, free, multi-user agricultural assistant for Indian farmers. It provides crop advisory, weather forecasts, plant disease detection, translation, analytics, and more, with both CLI and modern Kivy UI. It integrates local LLM (Ollama) for dynamic, conversational advice and tips.

## Features
- **Multi-user support:** Switch and manage user profiles, track history and metadata.
- **Crop Advisory:** Get structured and formatted advice for crops and soils.
- **Weather Forecast:** Automatically detects your location and displays a 7-day forecast using OpenWeatherMap API, plus LLM-generated farming tips.
- **Plant Disease Detection:** Upload leaf images, get disease predictions via Roboflow, and receive LLM-generated solutions and medicine recommendations.
- **FAQ & Guidance:** Ask questions and get answers from local LLM (Ollama) for dynamic, up-to-date advice.
- **Translation:** Translate text to major Indian languages offline.
- **Text-to-Speech:** Listen to advice and responses in your preferred language.
- **Analytics:** View user activity and crop trends.
- **Robust Logging:** All UI/CLI interactions are logged with timestamps and duplicate prevention.

## LLM Integration
- Uses [Ollama](https://ollama.com/) to run local models (e.g., llama3:8b) for:
  - FAQ responses
  - Weather tips
  - Plant disease solutions/medicine
  - Conversational agentic advice

## Setup
1. **Install Python 3.7+**
2. **Install dependencies:**
   ```sh
   pip install -r farmer_agent/requirements.txt
   ```
3. **Install Ollama and download a model:**
   - [Ollama install guide](https://ollama.com/download)
   - Example: `ollama pull llama3:8b`
   - Start Ollama server: `ollama serve`
4. **Set API keys:**
   - OpenWeatherMap: Set `OPENWEATHER_API_KEY` in your environment or `.env.local`
   - Roboflow: Set API key in `cv.py` if needed

## Usage
- **CLI:**
  ```sh
  python farmer_agent/main.py
  ```
- **UI:**
  ```sh
  python interface.py
  ```

## Data Files
- All static data (crops, market prices, soil, weather patterns) is in `farmer_agent/data/`

## How It Works
- **Weather:** Detects your city via IP, fetches 7-day forecast, and queries LLM for actionable tips.
- **Disease Detection:** Upload image, get prediction, and LLM-generated solution/medicine.
- **FAQ:** All questions answered by local LLM for dynamic, up-to-date advice.
- **User History:** All queries and advice are saved per user profile.

## Contributing
Pull requests and suggestions welcome!

## License
MIT
```bash
python farmer_agent/nlp/stt.py --mic           # Record from mic, auto language detection
python farmer_agent/nlp/stt.py --file path/to/audio.wav  # Transcribe audio file
```

**UI:**
Press the mic button to start recording, and press again to stop. The recognized text and detected language will be shown in the chat.

### Calendar & Reminders (CLI/UI)
- View crop schedules, list all crops, add/delete reminders, add recurring reminders, and get next activity for any crop.
- All features are available in both CLI and UI via menu or button.

### FAQ & Analytics
- Search FAQs by keyword, tag, or partial match.
- View user activity, crop trends, and feedback analytics.

### Weather
- Weather estimation uses OpenWeatherMap API (API key required in `env.local`).

## Example Output

**Speech-to-Text Example (UI):**
```
User presses mic button...
Recording... (speak in any supported language)
User presses mic button again.
Recognized Text: नमस्ते, मैं किसान हूँ
Detected Language: hi
```

```plaintext
Based on your input, we recommend the following: ...
Plant Type: Tomato
Diseases Detected: [Bacterial Spot]
Weather Data: {'temperature': 25, 'humidity': 70}
Soil Condition: Sandy Soil
Market Prices: {'Tomato': 1.50}

Crop Calendar Example:
```
Available crops: Tomato, Rice, ...
Schedule for Tomato:
{
  "sowing": "2025-07-01",
  "fertilizing": ["2025-07-10", "2025-07-20"],
  ...
}
Next activity for Tomato: fertilizing on 2025-07-20
```

Reminder Example:
```
Upcoming reminders:
[
  {"crop": "Tomato", "activity": "Fertilize", "date": "2025-07-20"},
  {"crop": "Rice", "activity": "Irrigate", "date": "2025-07-18"}
]
```
```

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.