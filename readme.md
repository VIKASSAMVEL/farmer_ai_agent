# Farmer Agent


The Farmer Agent is an AI-powered tool designed to provide tailored agricultural support to small-scale farmers and non-farmers across the world. It leverages natural language processing (NLP), computer vision, and real-time data integration to offer personalized guidance in various languages and mediums. The system now features a modern Kivy-based UI and a CLI, both with full feature parity.

## Key Features


1. **Voice, Text, and Image Input:** Easy communication through voice commands, text inputs, or image uploads.
2. **Multilingual NLP:** Understands and responds in regional languages and dialects.
3. **Plant Identification via Computer Vision:** Detects plant species and diseases using image input.
4. **Personalized Crop Advisory:** Integrates soil, weather, and market data to give tailored advice.
5. **Climate-Smart Recommendations:** Encourages sustainable practices and water-saving techniques.
6. **Offline Mode:** Basic features function without internet access (e.g., image diagnosis, preloaded guidance).
7. **Advanced Crop Calendar & Reminders:**
   - View crop schedules, list all crops, and get next scheduled activity for any crop.
   - Add one-time or recurring reminders for any crop activity.
   - Delete reminders by crop, activity, or date.
   - All calendar/reminder features available in both CLI and UI.
8. **Enhanced FAQ Module:**
   - Fuzzy/partial search, tag/category filtering, and related questions.
   - Large, plant-specific FAQ database.
9. **Analytics & Feedback:**
   - Collects user feedback on advisories and tracks engagement.
   - Provides user activity summaries, crop trends, and feedback analytics.
10. **Secure API Key Handling:**
    - Weather API key is loaded from `env.local` (excluded from git) and shared across modules.
    - No API keys are exposed in code or version control.
11. **Robust Error Handling:**
    - All modules handle missing dependencies gracefully.
    - UI and CLI both provide clear error messages and fallback options.

## Technical Requirements

- Python 3.7 or later
- pip (Python package installer)
- SpeechRecognition library for voice processing
- Transformers library from Hugging Face for NLP and computer vision
- Requests library for API integrations

## Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/farmer-agent.git
   cd farmer-agent
   ```


2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Weather API Key:**
   - Create a file named `env.local` in the project root with the following content:
     ```
     OPENWEATHER_API_KEY=your_openweather_api_key_here
     ```
   - The file is already excluded from git via `.gitignore`.

## Usage

### Launching the Agent

**CLI:**
```bash
python farmer_agent/main.py
```

**UI (Kivy):**
```bash
python farmer_agent/ui/interface.py
```

### Calendar & Reminders (CLI/UI)
- View crop schedules, list all crops, add/delete reminders, add recurring reminders, and get next activity for any crop.
- All features are available in both CLI and UI via menu or button.

### FAQ & Analytics
- Search FAQs by keyword, tag, or partial match.
- View user activity, crop trends, and feedback analytics.

### Weather
- Weather estimation uses OpenWeatherMap API (API key required in `env.local`).

## Example Output

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