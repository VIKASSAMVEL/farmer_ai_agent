# Farmer Agent

The Farmer Agent is an AI-powered tool designed to provide tailored agricultural support to small-scale farmers and non-farmers across the world. It leverages natural language processing (NLP), computer vision, and real-time data integration to offer personalized guidance in various languages and mediums.

## Key Features

1. **Voice, Text, and Image Input:** Easy communication through voice commands, text inputs, or image uploads.
2. **Multilingual NLP:** Understands and responds in regional languages and dialects.
3. **Plant Identification via Computer Vision:** Detects plant species and diseases using image input.
4. **Personalized Crop Advisory:** Integrates soil, weather, and market data to give tailored advice.
5. **Climate-Smart Recommendations:** Encourages sustainable practices and water-saving techniques.
6. **Offline Mode:** Basic features function without internet access (e.g., image diagnosis, preloaded guidance).

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

## Usage

### Voice Input

1. Run the script:
   ```bash
   python src/main.py
   ```
2. Speak your request into the microphone.

### Text Input

1. Create a text file with your request.
2. Run the script and provide the path to the text file:
   ```bash
   python src/main.py --input-file input.txt
   ```

### Image Input

1. Place an image of a plant in the `images` directory.
2. Run the script:
   ```bash
   python src/main.py --image-path images/plant.jpg
   ```

## Example Output

```plaintext
Based on your input, we recommend the following: ...
Plant Type: Tomato
Diseases Detected: [Bacterial Spot]
Weather Data: {'temperature': 25, 'humidity': 70}
Soil Condition: Sandy Soil
Market Prices: {'Tomato': 1.50}
```

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.