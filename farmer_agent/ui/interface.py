from kivy.uix.button import Button as KivyButton
from kivy.graphics import Color, RoundedRectangle
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout

import sys
import os
from utils.env_loader import load_env_local
sys.path.append('..')
try:
    from advisory.advisor import get_crop_advice
    from data.faq import FAQ
    from data.weather import WeatherEstimator
    from data.crop_calendar import CropCalendar, Reminders
    from nlp.stt import recognize_speech
    from nlp.tts import speak, list_voices
    from nlp.translate import OfflineTranslator
    from nlp.plant_cv import PlantIdentifier
    from utils.file_utils import load_json
    from data.user_profile import UserManager
    from data.analytics import Analytics
    from utils.accessibility import Accessibility
except Exception as e:
    print("Import error in interface.py:", e)
    get_crop_advice = None
    FAQ = None
    WeatherEstimator = None
    CropCalendar = None
    Reminders = None
    recognize_speech = None
    speak = None
    list_voices = None
    OfflineTranslator = None
    PlantIdentifier = None
    load_json = None
    UserManager = None
    Analytics = None
    Accessibility = None

# --- Custom iOS-style Button ---
class IOSButton(KivyButton):
    def __init__(self, **kwargs):
        super(IOSButton, self).__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0)
        self.color = (1, 1, 1, 1)
        self.font_size = 16
        self.size_hint = (None, None)
        self.size = (120, 40)
        self.radius = [20]
        # Ensure bind is called from the Kivy Button base class
        KivyButton.bind(self, pos=self.update_canvas, size=self.update_canvas)  # type: ignore
        with self.canvas.before:  # type: ignore
            Color(0.1, 0.1, 0.1, 1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=self.radius)

    def update_canvas(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

# --- Chat Bubble ---
class ChatBubble(Label):
    def __init__(self, text, is_user=False, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.size_hint_y = None
        self.height = self.texture_size[1] + 20
        self.halign = 'right' if is_user else 'left'
        self.valign = 'middle'
        self.padding = (10, 10)
        self.color = (1, 1, 1, 1) if is_user else (0.9, 0.9, 0.9, 1)
        self.text_size = (600, None)
        self.markup = True

# --- Main Chat Screen ---
class ChatScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'

        # --- Chat history area ---
        self.chat_history = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.chat_history.bind(minimum_height=self.chat_history.setter('height'))  # type: ignore
        self.scroll = ScrollView(size_hint=(1, 0.73))
        self.scroll.add_widget(self.chat_history)
        self.add_widget(self.scroll)

        # --- Input area ---
        input_layout = BoxLayout(size_hint=(1, 0.15))
        self.text_input = TextInput(size_hint=(0.8, 1), multiline=False)
        send_btn = IOSButton(text='Send', size_hint=(0.2, 1))
        send_btn.bind(on_press=self.send_message) # type: ignore
        input_layout.add_widget(self.text_input)
        input_layout.add_widget(send_btn)
        self.add_widget(input_layout)

        # --- Feature Buttons (iOS style, horizontal) ---
        feature_layout = BoxLayout(size_hint=(1, 0.12), spacing=8, padding=[8, 8, 8, 0])
        self.feature_buttons = {
            "Input": IOSButton(text="Input", on_press=self.input_action),
            "Advisory": IOSButton(text="Advisory", on_press=self.advisory_action),
            "Calendar": IOSButton(text="Calendar", on_press=self.calendar_action),
            "FAQ": IOSButton(text="FAQ", on_press=self.faq_action),
            "Weather": IOSButton(text="Weather", on_press=self.weather_action),
            "Analytics": IOSButton(text="Analytics", on_press=self.analytics_action),
            "TTS Voices": IOSButton(text="TTS Voices", on_press=self.tts_voices_action),
            "Exit": IOSButton(text="Exit", on_press=self.exit_action),
        }
        for btn in self.feature_buttons.values():
            feature_layout.add_widget(btn)
        self.add_widget(feature_layout)
    def input_action(self, instance):
        self.add_bubble("Input Modes: 1. Voice 2. Text 3. Image", is_user=False)
        self.awaiting_input_mode = True

    def tts_voices_action(self, instance):
        if list_voices:
            import io
            import contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                list_voices()
            voices = buf.getvalue()
            self.add_bubble("Available TTS Voices:", is_user=False)
            self.add_bubble(voices, is_user=False)
        else:
            self.add_bubble("TTS Voices module not available.", is_user=False)

        # --- Chat history area ---
        self.chat_history = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.chat_history.bind(minimum_height=self.chat_history.setter('height'))  # type: ignore
        self.scroll = ScrollView(size_hint=(1, 0.73))
        self.scroll.add_widget(self.chat_history)
        self.add_widget(self.scroll)

        # --- Input area ---
        input_layout = BoxLayout(size_hint=(1, 0.15))
        self.text_input = TextInput(size_hint=(0.8, 1), multiline=False)
        send_btn = IOSButton(text='Send', size_hint=(0.2, 1))
        send_btn.bind(on_press=self.send_message) # type: ignore
        input_layout.add_widget(self.text_input)
        input_layout.add_widget(send_btn)
        self.add_widget(input_layout)

        # --- State flags ---
        self.awaiting_advisory = False
        self.awaiting_faq = False
        self.awaiting_weather = False
        self.awaiting_calendar = False
        self.awaiting_input_mode = False
        self.awaiting_text_input = False
        self.awaiting_image_path = False
        self.awaiting_add_reminder = False
        self.awaiting_reminder_activity = False
        self.awaiting_reminder_days = False
        self.awaiting_analytics = False

    # --- Feature Actions ---
    def advisory_action(self, instance):
        self.add_bubble("Please enter your crop name for advisory:", is_user=False)
        self.awaiting_advisory = True


    def faq_action(self, instance):
        if FAQ:
            self.add_bubble("Please enter your question or keyword for FAQ:", is_user=False)
            self.awaiting_faq = True
        else:
            self.add_bubble("FAQ module not available.", is_user=False)

    def weather_action(self, instance):
        if WeatherEstimator:
            load_env_local()
            self._openweather_api_key = os.environ.get('OPENWEATHER_API_KEY')
            self.weather_inputs = {}
            self.add_bubble("Enter season (summer/monsoon/winter, blank for auto):", is_user=False)
            self.awaiting_weather_season = True
        else:
            self.add_bubble("Weather module not available.", is_user=False)

    def calendar_action(self, instance):
        if CropCalendar:
            self.add_bubble("Calendar options: 1. View crop schedule 2. List crops 3. Add reminder 4. Add recurring reminder 5. Delete reminder 6. Next activity\nEnter option number:", is_user=False)
            self.awaiting_calendar_option = True
        else:
            self.add_bubble("Calendar module not available.", is_user=False)
    def handle_calendar_option(self, user_text):
        option = user_text.strip()
        from data.crop_calendar import CropCalendar as CropCalendarClass, Reminders as RemindersClass
        self.calendar = CropCalendarClass()
        self.reminders = RemindersClass()
        if option == "1":
            self.add_bubble("Enter crop name:", is_user=False)
            self.awaiting_calendar_crop = True
        elif option == "2":
            crops = self.calendar.list_crops() if self.calendar else []
            self.add_bubble("Available crops: " + ", ".join(crops), is_user=False)
        elif option == "3":
            self.add_bubble("Enter crop name for reminder:", is_user=False)
            self.awaiting_reminder_crop = True
        elif option == "4":
            self.add_bubble("Enter crop name for recurring reminder:", is_user=False)
            self.awaiting_recurring_crop = True
        elif option == "5":
            self.add_bubble("Enter crop name to delete reminders:", is_user=False)
            self.awaiting_delete_crop = True
        elif option == "6":
            self.add_bubble("Enter crop name for next activity:", is_user=False)
            self.awaiting_next_activity_crop = True
        else:
            self.add_bubble("Invalid option.", is_user=False)

    def analytics_action(self, instance):
        self.add_bubble("Analytics feature coming soon!", is_user=False)

    def exit_action(self, instance):
        self.add_bubble("Goodbye! Close the window to exit.", is_user=False)

    # --- Main Message Handler ---
    def send_message(self, instance):
        user_text = self.text_input.text.strip()
        if not user_text:
            return
        self.add_bubble(user_text, is_user=True)
        try:
            if self.awaiting_input_mode:
                mode = user_text.strip()
                if mode == "1" and recognize_speech:
                    text = recognize_speech()
                    self.add_bubble(f"Recognized Text: {text}", is_user=False)
                    if speak:
                        speak(text)
                elif mode == "2":
                    self.add_bubble("Enter your request:", is_user=False)
                    self.awaiting_text_input = True
                elif mode == "3" and PlantIdentifier:
                    self.add_bubble("Enter image path:", is_user=False)
                    self.awaiting_image_path = True
                else:
                    self.add_bubble("Invalid input mode or module not available.", is_user=False)
                self.awaiting_input_mode = False
            elif self.awaiting_text_input:
                text = user_text.strip()
                self.add_bubble(f"Text: {text}", is_user=False)
                if speak:
                    speak(text)
                self.awaiting_text_input = False
            elif self.awaiting_image_path:
                image_path = user_text.strip()
                if PlantIdentifier:
                    identifier = PlantIdentifier()
                    result = identifier.identify(image_path)
                    self.add_bubble(f"Plant Identification Result: {result}", is_user=False)
                else:
                    self.add_bubble("PlantIdentifier module not available.", is_user=False)
                self.awaiting_image_path = False
            elif self.awaiting_advisory:
                if get_crop_advice:
                    crop = user_text.strip()
                    soil = ''  # Optionally prompt for soil in a second step
                    self._last_advisory_crop = crop
                    self._last_advisory_soil = soil
                    advice = get_crop_advice(crop, soil if soil else None)
                    self._last_advisory = advice
                    self.add_bubble("Personalized Advisory:", is_user=False)
                    import json
                    self.add_bubble(json.dumps(advice, indent=2, ensure_ascii=False), is_user=False)
                    self.add_bubble("Was this advice helpful? (y/n):", is_user=False)
                    self.awaiting_advisory_feedback = True
                else:
                    self.add_bubble("Advisory module not available.", is_user=False)
                self.awaiting_advisory = False
            elif hasattr(self, 'awaiting_advisory_feedback') and self.awaiting_advisory_feedback:
                feedback = user_text.strip().lower()
                feedback_val = 'positive' if feedback == 'y' else ('negative' if feedback == 'n' else None)
                if hasattr(self, '_last_advisory') and isinstance(self._last_advisory, dict):
                    if feedback_val:
                        self._last_advisory['feedback'] = feedback_val
                # Optionally, store feedback in user profile if available
                try:
                    from data.user_profile import UserManager
                    manager = UserManager()
                    user = manager.current_user if hasattr(manager, 'current_user') else None
                    if user:
                        user.add_query(f"{getattr(self, '_last_advisory_crop', '')}, {getattr(self, '_last_advisory_soil', '')}", self._last_advisory)
                except Exception:
                    pass
                self.add_bubble("Thank you for your feedback!", is_user=False)
                self.awaiting_advisory_feedback = False
            elif self.awaiting_faq:
                if FAQ:
                    faq = FAQ()
                    results = faq.search(user_text)
                    self.add_bubble("FAQ Results:", is_user=False)
                    import json
                    self.add_bubble(json.dumps(results, indent=2, ensure_ascii=False), is_user=False)
                else:
                    self.add_bubble("FAQ module not available.", is_user=False)
                self.awaiting_faq = False
            elif hasattr(self, 'awaiting_weather_online') and self.awaiting_weather_online:
                self.weather_inputs['use_online'] = user_text.strip().lower() == 'y'
                self.add_bubble("Enter season (summer/monsoon/winter, blank for auto):", is_user=False)
                self.awaiting_weather_online = False
                self.awaiting_weather_season = True
            elif hasattr(self, 'awaiting_weather_season') and self.awaiting_weather_season:
                self.weather_inputs = getattr(self, 'weather_inputs', {})
                self.weather_inputs['season'] = user_text.strip() or None
                self.add_bubble("Enter location (optional):", is_user=False)
                self.awaiting_weather_season = False
                self.awaiting_weather_location = True
            elif hasattr(self, 'awaiting_weather_location') and self.awaiting_weather_location:
                self.weather_inputs['location'] = user_text.strip() or None
                self.add_bubble("Enter crop (optional):", is_user=False)
                self.awaiting_weather_location = False
                self.awaiting_weather_crop = True
            elif hasattr(self, 'awaiting_weather_crop') and self.awaiting_weather_crop:
                self.weather_inputs['crop'] = user_text.strip() or None
                self.add_bubble("Enter date (YYYY-MM-DD, blank for today):", is_user=False)
                self.awaiting_weather_crop = False
                self.awaiting_weather_date = True
            elif hasattr(self, 'awaiting_weather_date') and self.awaiting_weather_date:
                from datetime import datetime
                date_str = user_text.strip()
                date = None
                if date_str:
                    try:
                        date = datetime.strptime(date_str, "%Y-%m-%d")
                    except Exception:
                        self.add_bubble("Invalid date format, using today.", is_user=False)
                self.weather_inputs['date'] = date
                if WeatherEstimator:
                    estimator = WeatherEstimator(openweather_api_key=self._openweather_api_key)
                    weather = estimator.estimate(
                        season=self.weather_inputs.get('season'),
                        location=self.weather_inputs.get('location'),
                        crop=self.weather_inputs.get('crop'),
                        date=self.weather_inputs.get('date'),
                        use_online=True,
                        prefer_openweather=True
                    )
                    self.add_bubble("Weather Estimation:", is_user=False)
                    self.add_bubble(f"Temperature: {weather.get('temperature', 'N/A')}°C", is_user=False)
                    self.add_bubble(f"Humidity: {weather.get('humidity', 'N/A')}%", is_user=False)
                    self.add_bubble(f"Rainfall: {weather.get('rainfall', 'N/A')} mm", is_user=False)
                    self.add_bubble(f"Wind: {weather.get('wind', 'N/A')}", is_user=False)
                    self.add_bubble(f"Advice: {weather.get('advice', 'N/A')}", is_user=False)
                    warnings = weather.get('warnings', [])
                    if warnings:
                        self.add_bubble("Warnings:", is_user=False)
                        for w in warnings:
                            self.add_bubble(f"- {w}", is_user=False)
                else:
                    self.add_bubble("Weather module not available.", is_user=False)
                self.awaiting_weather_date = False
            elif hasattr(self, 'awaiting_calendar_option') and self.awaiting_calendar_option:
                self.handle_calendar_option(user_text)
                self.awaiting_calendar_option = False
            elif hasattr(self, 'awaiting_calendar_crop') and self.awaiting_calendar_crop:
                crop = user_text.strip()
                self.last_calendar_crop = crop
                import json
                self.add_bubble("Crop Calendar:", is_user=False)
                if self.calendar:
                    self.add_bubble(json.dumps(self.calendar.get_schedule(crop), indent=2, ensure_ascii=False), is_user=False)
                self.add_bubble("Reminders:", is_user=False)
                if self.reminders:
                    self.add_bubble(json.dumps(self.reminders.get_upcoming(), indent=2, ensure_ascii=False), is_user=False)
                self.awaiting_calendar_crop = False
            elif hasattr(self, 'awaiting_reminder_crop') and self.awaiting_reminder_crop:
                self.reminder_crop = user_text.strip()
                self.add_bubble("Activity:", is_user=False)
                self.awaiting_reminder_activity = True
                self.awaiting_reminder_crop = False
            elif hasattr(self, 'awaiting_reminder_activity') and self.awaiting_reminder_activity:
                self.reminder_activity = user_text.strip()
                self.add_bubble("Days from now:", is_user=False)
                self.awaiting_reminder_days = True
                self.awaiting_reminder_activity = False
            elif hasattr(self, 'awaiting_reminder_days') and self.awaiting_reminder_days:
                days = None
                try:
                    days = int(user_text.strip())
                except Exception:
                    self.add_bubble("Error: Invalid number of days.", is_user=False)
                if days is not None and self.reminders:
                    self.reminders.add_reminder(self.reminder_crop, self.reminder_activity, days)
                    self.add_bubble("Reminder added.", is_user=False)
                self.awaiting_reminder_days = False
            elif hasattr(self, 'awaiting_recurring_crop') and self.awaiting_recurring_crop:
                self.recurring_crop = user_text.strip()
                self.add_bubble("Activity:", is_user=False)
                self.awaiting_recurring_activity = True
                self.awaiting_recurring_crop = False
            elif hasattr(self, 'awaiting_recurring_activity') and self.awaiting_recurring_activity:
                self.recurring_activity = user_text.strip()
                self.add_bubble("Start in how many days?:", is_user=False)
                self.awaiting_recurring_start = True
                self.awaiting_recurring_activity = False
            elif hasattr(self, 'awaiting_recurring_start') and self.awaiting_recurring_start:
                try:
                    self.recurring_start = int(user_text.strip())
                    self.add_bubble("Interval (days):", is_user=False)
                    self.awaiting_recurring_interval = True
                except Exception as e:
                    self.add_bubble(f"Error: {str(e)}", is_user=False)
                self.awaiting_recurring_start = False
            elif hasattr(self, 'awaiting_recurring_interval') and self.awaiting_recurring_interval:
                try:
                    self.recurring_interval = int(user_text.strip())
                    self.add_bubble("Occurrences:", is_user=False)
                    self.awaiting_recurring_occurrences = True
                except Exception as e:
                    self.add_bubble(f"Error: {str(e)}", is_user=False)
                self.awaiting_recurring_interval = False
            elif hasattr(self, 'awaiting_recurring_occurrences') and self.awaiting_recurring_occurrences:
                try:
                    occurrences = int(user_text.strip())
                    if self.reminders:
                        self.reminders.add_recurring_reminder(self.recurring_crop, self.recurring_activity, self.recurring_start, self.recurring_interval, occurrences)
                        self.add_bubble("Recurring reminder(s) added.", is_user=False)
                except Exception as e:
                    self.add_bubble(f"Error: {str(e)}", is_user=False)
                self.awaiting_recurring_occurrences = False
            elif hasattr(self, 'awaiting_delete_crop') and self.awaiting_delete_crop:
                crop = user_text.strip()
                if self.reminders:
                    self.reminders.delete_reminder(crop)
                    self.add_bubble(f"All reminders for {crop} deleted.", is_user=False)
                self.awaiting_delete_crop = False
            elif hasattr(self, 'awaiting_next_activity_crop') and self.awaiting_next_activity_crop:
                crop = user_text.strip()
                next_act = self.calendar.next_activity(crop) if self.calendar else None  # type: ignore[attr-defined]
                if next_act:
                    self.add_bubble(f"Next activity for {crop}: {next_act['activity']} on {next_act['date']}", is_user=False)
                else:
                    self.add_bubble(f"No upcoming activities for {crop}.", is_user=False)
                self.awaiting_next_activity_crop = False
            elif self.awaiting_add_reminder:
                answer = user_text.strip().lower()
                if answer == 'y':
                    self.add_bubble("Activity:", is_user=False)
                    self.awaiting_reminder_activity = True
                else:
                    self.add_bubble("No reminder added.", is_user=False)
                self.awaiting_add_reminder = False
            elif self.awaiting_reminder_activity:
                self.reminder_activity = user_text.strip()
                self.add_bubble("Days from now:", is_user=False)
                self.awaiting_reminder_days = True
                self.awaiting_reminder_activity = False
            elif self.awaiting_reminder_days:
                try:
                    days = int(user_text.strip())
                    crop = getattr(self, 'last_calendar_crop', 'Unknown')
                    if Reminders:
                        reminders = Reminders()
                        try:
                            reminders.add_reminder(crop, self.reminder_activity, days)
                            self.add_bubble("Reminder added.", is_user=False)
                        except Exception as e:
                            self.add_bubble(f"Error adding reminder: {str(e)}", is_user=False)
                    else:
                        self.add_bubble("Reminders module not available.", is_user=False)
                except Exception as e:
                    self.add_bubble(f"Error: {str(e)}", is_user=False)
                self.awaiting_reminder_days = False
            elif self.awaiting_analytics:
                if Analytics:
                    try:
                        analytics = Analytics()
                        username = user_text.strip()
                        self.add_bubble("User Activity Summary:", is_user=False)
                        import json
                        self.add_bubble(json.dumps(analytics.user_activity_summary(username), indent=2, ensure_ascii=False), is_user=False)
                        self.add_bubble("Crop Trends:", is_user=False)
                        self.add_bubble(json.dumps(analytics.crop_trends(), indent=2, ensure_ascii=False), is_user=False)
                    except Exception as e:
                        self.add_bubble(f"Error in analytics: {str(e)}", is_user=False)
                else:
                    self.add_bubble("Analytics module not available.", is_user=False)
                self.awaiting_analytics = False
            else:
                try:
                    agent_response = self.get_agent_response(user_text)
                    self.add_bubble(agent_response, is_user=False)
                except Exception as e:
                    self.add_bubble(f"Error: {str(e)}", is_user=False)
        except Exception as e:
            self.add_bubble(f"Critical error: {str(e)}", is_user=False)
        self.text_input.text = ''

    # --- Utility Methods ---
    def add_bubble(self, text, is_user=False):
        bubble = ChatBubble(text, is_user=is_user)
        self.chat_history.add_widget(bubble)
        self.chat_history.height = self.chat_history.minimum_height
        self.scroll.scroll_y = 0

    def get_agent_response(self, user_text):
        text = user_text.lower()
        if 'advice' in text or 'advisory' in text or 'crop' in text:
            if get_crop_advice:
                crop = self.extract_crop(text)
                soil = self.extract_soil(text)
                advice = get_crop_advice(crop, soil)
                return f"Advisory for {crop} ({soil}):\n" + str(advice)
            else:
                return "Advisory module not available."
        elif 'faq' in text or 'question' in text:
            if FAQ:
                faq = FAQ()
                results = faq.search(text)
                if results:
                    return "\n".join([f"Q: {item['question']}\nA: {item['answer']}" for item in results])
                else:
                    return "No matching FAQ found."
            else:
                return "FAQ module not available."
        elif 'weather' in text:
            if WeatherEstimator:
                estimator = WeatherEstimator()
                weather = estimator.estimate()
                return f"Weather Estimation:\n" + str(weather)
            else:
                return "Weather module not available."
        elif 'calendar' in text:
            if CropCalendar:
                calendar = CropCalendar()
                crop = self.extract_crop(text)
                schedule = calendar.get_schedule(crop)
                return f"Crop Calendar for {crop}:\n" + str(schedule)
            else:
                return "Calendar module not available."
        else:
            return "Sorry, I didn't understand. Try asking for advice, FAQ, weather, or calendar."

    def extract_crop(self, text):
        # Simple crop extraction (improve with NLP if needed)
        for crop in ['tomato', 'rice']:
            if crop in text:
                return crop.capitalize()
        return 'Tomato'

    def extract_soil(self, text):
        for soil in ['sandy loam', 'clay loam']:
            if soil in text:
                return soil.title()
        return None

    def parse_crop_soil(self, text):
        # Simple parser for 'Advice for [crop] in [soil]'
        import re
        match = re.search(r'advice for ([\w ]+) in ([\w ]+)', text.lower())
        if match:
            crop = match.group(1).strip().title()
            soil = match.group(2).strip().title()
            return crop, soil
        # Fallback: try to find crop and soil words
        crops = ['Tomato', 'Rice']
        soils = ['Sandy Loam', 'Clay Loam']
        crop = next((c for c in crops if c.lower() in text.lower()), None)
        soil = next((s for s in soils if s.lower() in text.lower()), None)
        return crop, soil

# --- Kivy App Runner ---
class FarmerAgentApp(App):
    def build(self):
        return ChatScreen()

if __name__ == "__main__":
    FarmerAgentApp().run()