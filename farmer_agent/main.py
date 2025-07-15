def agentic_response(user_query, plant_result=None):
    # Load static data
    with open('farmer_agent/data/faq.json', 'r', encoding='utf-8') as f:
        faq_data = json.load(f)
    with open('farmer_agent/data/market_prices.json', 'r', encoding='utf-8') as f:
        market_data = json.load(f)
    # Compose prompt for LLM (replace with your LLM call)
    prompt = f"User question: {user_query}\n"
    if plant_result:
        prompt += f"Plant disease detection: {plant_result}\n"
    prompt += f"FAQs: {json.dumps(faq_data)}\n"
    prompt += f"Market prices: {json.dumps(market_data)}\n"
    prompt += "Answer the user's question using the above data."
    # Call your LLM here (pseudo)
    # response = llm_api.generate(prompt)
    response = "[LLM response placeholder]"  # Replace with actual LLM call
    return response
# Main entry point for Farmer Agent (offline, free)

# Unified Farmer Agent Main Script (Offline)
import sys
import sys
import os
from farmer_agent.utils.env_loader import load_env_local
import json
from farmer_agent.advisory.advisor import get_crop_advice
from farmer_agent.nlp.stt import recognize_speech
from farmer_agent.nlp.tts import speak, list_voices
from farmer_agent.nlp.translate import OfflineTranslator
from farmer_agent.nlp.cv import PlantIdentifier
from farmer_agent.utils.file_utils import load_json
from farmer_agent.data.user_profile import UserManager
from farmer_agent.data.crop_calendar import CropCalendar, Reminders
from farmer_agent.data.faq import FAQ
from farmer_agent.data.weather import WeatherEstimator
from farmer_agent.data.analytics import Analytics
from farmer_agent.utils.accessibility import Accessibility

def main():
    print("\n=== Farmer Agent ===")
    # Multi-user support
    manager = UserManager()
    print("Existing users:", manager.list_users())
    username = input("Enter username to switch or create: ")
    manager.add_user(username)
    user = manager.switch_user(username)

    # Accessibility options
    acc = Accessibility(
        large_text=input("Large text mode? (y/n): ").lower() == 'y',
        high_contrast=input("High contrast mode? (y/n): ").lower() == 'y',
        voice_nav=input("Voice navigation? (y/n): ").lower() == 'y'
    )

    # Weather API key prompt (optional)
    # Load OpenWeatherMap API key from env.local or environment
    if 'load_env_local' in globals() and callable(load_env_local):
        load_env_local()
    openweather_api_key = os.environ.get('OPENWEATHER_API_KEY')
    while True:
        print(acc.format_text("Select Feature:"))
        print("1. Input (Voice/Text/Image)")
        print("2. Crop Advisory")
        print("3. Crop Calendar & Reminders")
        print("4. FAQ & Guidance")
        print("5. Weather Estimation")
        print("6. Analytics")
        print("7. List TTS Voices")
        print("8. Translate Text")
        print("9. Exit")
        choice = input("Enter choice: ").strip()

        if choice == "1":
            print("Input Modes: 1. Voice (mic) 2. Audio File 3. Text 4. Image")
            mode = input("Enter input mode: ").strip()
            if mode == "1":
                lang = input("Language code (default: en): ").strip() or "en"
                result = recognize_speech(source="mic", lang=lang)
                text = result.get("text", "") if isinstance(result, dict) else result
                print(acc.apply_contrast(f"Transcribed Text: {text}"))
                acc.speak_text(text)
            elif mode == "2":
                file_path = input("Enter audio file path: ").strip()
                lang = input("Language code (default: auto): ").strip() or "auto"
                result = recognize_speech(source="file", file_path=file_path, lang=lang)
                text = result.get("text", "") if isinstance(result, dict) else result
                print(acc.apply_contrast(f"Transcribed Text: {text}"))
                acc.speak_text(text)
            elif mode == "3":
                text = input("Enter your request: ")
                print(acc.apply_contrast(f"Text: {text}"))
                acc.speak_text(text)
            elif mode == "4":
                image_path = input("Enter image path: ")
                identifier = PlantIdentifier()
                result = identifier.identify(image_path)
                print(acc.apply_contrast(f"Plant Identification Result: {result}"))
            else:
                print("Invalid mode.")
        elif choice == "2":
            crop = input("Enter crop name for advisory: ")
            soil = input("Enter soil type (optional): ")
            advice = get_crop_advice(crop, soil if soil else None)
            print(acc.format_text("\n=== STRUCTURED ADVISORY ==="))
            print(json.dumps(advice, indent=2, ensure_ascii=False))
            print(acc.format_text("\n=== FORMATTED ADVISORY ==="))
            print(advice['formatted'])
            # Speak first care instruction if available
            if advice.get('care_instructions'):
                acc.speak_text(advice['care_instructions'][0])
            # Collect feedback
            feedback = input("Was this advice helpful? (y/n): ").strip().lower()
            feedback_val = 'positive' if feedback == 'y' else ('negative' if feedback == 'n' else None)
            # Store feedback in the advisory dict for analytics
            if feedback_val:
                advice['feedback'] = feedback_val
            user.add_query(f"{crop}, {soil}", advice)
        elif choice == "3":
            calendar = CropCalendar()
            print(acc.format_text("Crop Calendar:"))
            crop = input("Enter crop name: ")
            print(json.dumps(calendar.get_schedule(crop), indent=2, ensure_ascii=False))
            reminders = Reminders()
            print(acc.format_text("Reminders:"))
            print(json.dumps(reminders.get_upcoming(), indent=2, ensure_ascii=False))
            if input("Add reminder? (y/n): ").lower() == 'y':
                activity = input("Activity: ")
                days = int(input("Days from now: "))
                reminders.add_reminder(crop, activity, days)
        elif choice == "4":
            query = input("Enter your FAQ question: ")
            faq = FAQ()
            results = faq.search(query, use_llm=True)
            if results:
                answer = results[0].get('answer', '')
                print(f"LLM FAQ Response:\n{answer}")
                speak(answer)
            else:
                print("No response from LLM.")
        elif choice == "5":
            estimator = WeatherEstimator(openweather_api_key=openweather_api_key)
            location = estimator.get_current_location()
            if location:
                print(acc.format_text(f"Detected location: {location}"))
                weekly = estimator.fetch_weekly_forecast(location)
                if weekly:
                    print(acc.format_text(f"7-Day Weather Forecast for {location}:"))
                    print(json.dumps(weekly, indent=2, ensure_ascii=False))
                    tips = estimator.get_llm_weather_tips(weekly)
                    print(acc.format_text("\nLLM Tips for Farmers:"))
                    print(tips)
                else:
                    print(acc.format_text("Could not fetch weekly forecast. Check API key or location."))
            else:
                print(acc.format_text("Could not detect location."))
        elif choice == "6":
            analytics = Analytics()
            print(acc.format_text("User Activity Summary:"))
            print(json.dumps(analytics.user_activity_summary(username), indent=2, ensure_ascii=False))
            print(acc.format_text("Crop Trends:"))
            print(json.dumps(analytics.crop_trends(), indent=2, ensure_ascii=False))
        elif choice == "7":
            print(acc.format_text("Available TTS Voices:"))
            list_voices()
        elif choice == "8":
            text = input("Enter text to translate: ")
            tgt_lang = input("Enter target language code (hi=Hindi, ta=Tamil, te=Telugu, kn=Kannada, ml=Malayalam): ").strip() or "hi"
            from nlp.translate import OfflineTranslator
            translator = OfflineTranslator()
            translated = translator.translate(text, "en", tgt_lang)
            if translated.startswith("[Error]"):
                print(acc.format_text(f"Translation failed: {translated}"))
            else:
                print(acc.format_text(f"Translation: {translated}"))
        elif choice == "9":
            print(acc.format_text("Goodbye!"))
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()