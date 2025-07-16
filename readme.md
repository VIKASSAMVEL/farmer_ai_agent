# Farmer AI Agent


**An offline-first, AI-powered agricultural assistant with a modern, accessible, multilingual chat UI (English, Tamil, Hindi), LLM-powered translation, robust voice and image input, and advanced reminders/calendar tools for Indian farmers.**


The Farmer AI Agent is a comprehensive solution that combines local data, machine learning models, and an intuitive, accessible user interface to address the daily challenges faced by farmers. It operates primarily offline, with optional online features for enhanced, real-time data.

![Screenshot of Farmer AI Agent Kivy GUI showing multilingual chat, calendar options as buttons, and accessible design](image.png)

---

## ✨ Core Features

The project is built on a modular architecture, with distinct components for each key function:


*   **Multilingual, Accessible Chat UI:**
    *   Modern chat-based interface with support for English, Tamil, and Hindi (UI and backend).
    *   Language dropdown with correct font rendering for Indian languages.
    *   Visual feedback for language selection and button-like dropdown options.
    *   All UI elements (labels, buttons, chat bubbles) render Tamil/Hindi text natively.
    *   Accessibility-focused: large fonts, color contrast, and alt text for images.

*   **Personalized Crop Advisory:** Get tailored advice for specific crops (e.g., Tomato, Rice, Wheat). The agent considers soil type and provides recommendations on best practices, climate-smart tips, and care instructions using local data.

*   **🌿 Plant Disease Identification (CV):** Upload an image of a plant leaf, and the agent will use a computer vision model (via Roboflow) to identify potential diseases. It then leverages a local LLM to provide practical solutions and medicine recommendations.

*   **☀️ Smart Weather Forecasting:**
    *   **Online:** Fetches a 7-day forecast using the OpenWeatherMap API, detecting the user's location automatically.
    *   **Offline:** Falls back to seasonal weather patterns if offline.
    *   **LLM-Powered Tips:** Generates practical farming tips (e.g., for irrigation, disease prevention) based on the weekly forecast.


*   **🗣️ Advanced NLP Suite (Offline):**
    *   **Speech-to-Text:** Transcribe voice commands and queries from a microphone or audio file using OpenAI's Whisper model, with support for major Indian languages. Mic input now waits for user to stop and handles language codes robustly.
    *   **Text-to-Speech:** Reads out responses and guidance using the system's installed voices.
    *   **Offline & LLM-Powered Translation:** Translate text between English, Hindi, Tamil (UI and backend) using MarianMT, IndicTrans2, and local LLMs. LLM-based translation is used for all agent responses in the selected language.

*   **❓ FAQ & Guidance:** Ask questions in natural language. The agent uses a local LLM (if available) or a static FAQ database to provide answers on a wide range of farming topics.


*   **📅 Crop Calendar & Reminders:**
    *   Calendar and reminder options are displayed as interactive buttons in the chat UI (not just text input).
    *   Backend and UI options are always synchronized; both label and number input are accepted.
    *   View detailed activity schedules for various crops.
    *   Set one-time or recurring reminders for crucial farming tasks like fertilizing, irrigating, and harvesting.
    *   Check the next upcoming activity for a specific crop.

*   **📊 User Profiles & Analytics:**
    *   Supports multiple user profiles to keep a history of queries and advice.
    *   Analyzes interaction data to identify crop trends and measure the effectiveness of the advice provided.


*   **💻 Dual Interfaces:**
    *   **Graphical User Interface (GUI):**
        *   Modern, chat-based interface built with KivyMD.
        *   Multilingual (English, Tamil, Hindi) with correct font rendering.
        *   Chat mode is default; direct LLM chat enabled.
        *   Calendar/reminder options as buttons.
        *   Visual feedback and accessibility improvements.
    *   **Command-Line Interface (CLI):** A lightweight, menu-driven interface for users who prefer the terminal.

---

## 🛠️ Technology Stack

*   **Backend:** Python
*   **GUI:** Kivy
*   **Machine Learning & NLP:**
    *   `transformers` (Hugging Face) for offline translation.
    *   `openai-whisper` for speech-to-text.
    *   `inference-sdk` for Roboflow computer vision.
    *   `pyttsx3` for text-to-speech.
*   **Local LLM Integration:** Ollama (supports models like Llama 3, Mistral).
*   **Data Handling:** JSON for local databases and configuration.

---

## 🏗️ Architecture

The project follows a clean, modular structure that separates core logic from the user interface.

*   `farmer_agent/`: Contains all the core backend logic.
    *   `advisory/`: Generates crop advice.
    *   `data/`: Holds all offline data files (FAQs, crop calendars, user history, etc.).
    *   `nlp/`: Manages all Natural Language Processing tasks (STT, TTS, CV, Translate).
    *   `utils/`: Helper functions for file handling, environment loading, and accessibility.
    *   `config/`: Configuration files like crop definitions.
*   `main.py`: The entry point for the Command-Line Interface (CLI).
*   `test_kivy.py`: The entry point for the Kivy Graphical User Interface (GUI).
*   `data/`: This directory is crucial as it stores the "brain" of the agent in an offline context.

This offline-first approach ensures that the agent remains functional even without an internet connection, with online services acting as an enhancement.

---

## 🚀 Getting Started

Follow these steps to set up and run the Farmer AI Agent on your local machine.

### 1. Prerequisites

*   Python 3.8+
*   Git
*   (Optional but Recommended) Ollama for running a local LLM. After installing, pull a model:
    ```sh
    ollama pull phi3:mini
    ```

### 2. Clone the Repository

```sh
git clone <your-repository-url>
cd farmer_ai_agent
```

### 3. Install Dependencies

It is recommended to use a virtual environment.

```sh
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

Install the required packages. Note that `torch` and `pyaudio` may have system-specific installation steps.

```sh
# First, install PyTorch from the official site: https://pytorch.org/get-started/locally/
# Example for CPU:
pip install torch torchvision torchaudio

# Then install the rest of the requirements
pip install kivy openai-whisper pyttsx3 requests transformers inference-sdk sentencepiece

# For microphone input
pip install pyaudio
```

### 4. Configure Environment Variables

Create a file named `env.local` in the project root directory. This file is used to store API keys securely.

```
# env.local

# For real-time weather forecasts (optional)
OPENWEATHER_API_KEY=your_openweathermap_api_key
```


### 5. Run the Application

You can run either the GUI or the CLI.

**To run the Kivy GUI (with multilingual chat, calendar/reminder buttons, and LLM translation):**

```sh
python test_kivy.py
```

**To run the CLI:**

```sh
python farmer_agent/main.py
```

---


## ⚙️ Configuration

The agent's knowledge base is stored in JSON files within the `farmer_agent/data/` and `farmer_agent/config/` directories. You can customize and expand the agent's capabilities by editing these files:

*   `farmer_agent/config/crops.json`: Add or modify crop-specific data, care instructions, and tips.
*   `farmer_agent/data/faq.json`: Expand the FAQ database with more questions and answers.
*   `farmer_agent/data/crop_calendar.json`: Define or update crop schedules and calendar/reminder options (these are now reflected in the UI as buttons).
*   `farmer_agent/data/soil_data.json`: Add information about different soil types.
*   `farmer_agent/data/market_prices.json`: Update market price information.

---


## 🤝 Contributing

Contributions are welcome! If you have an idea for a new feature, language, or accessibility improvement, or have found a bug, please open an issue to discuss it first.

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/YourFeature`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add some feature'`).
5.  Push to the branch (`git push origin feature/YourFeature`).
6.  Open a Pull Request.

---

## 📜 License

This project is licensed under the MIT License. See the `LICENSE` file for details.