from kivy.uix.button import Button as KivyButton
from kivy.graphics import Color, RoundedRectangle
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout

import sys
sys.path.append('..')
try:
    from advisory.advisor import get_crop_advice
    from data.faq import FAQ
    from data.weather import WeatherEstimator
    from data.crop_calendar import CropCalendar
except Exception as e:
    print("Import error in interface.py:", e)
    get_crop_advice = None
    FAQ = None
    WeatherEstimator = None
    CropCalendar = None

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

        # --- Feature Buttons (iOS style, horizontal) ---
        feature_layout = BoxLayout(size_hint=(1, 0.12), spacing=8, padding=[8, 8, 8, 0])
        self.feature_buttons = {
            "Advisory": IOSButton(text="Advisory", on_press=self.advisory_action),
            "FAQ": IOSButton(text="FAQ", on_press=self.faq_action),
            "Weather": IOSButton(text="Weather", on_press=self.weather_action),
            "Calendar": IOSButton(text="Calendar", on_press=self.calendar_action),
            "Analytics": IOSButton(text="Analytics", on_press=self.analytics_action),
            "Exit": IOSButton(text="Exit", on_press=self.exit_action),
        }
        for btn in self.feature_buttons.values():
            feature_layout.add_widget(btn)
        self.add_widget(feature_layout)

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

    # --- Feature Actions ---
    def advisory_action(self, instance):
        self.add_bubble("Please enter your crop and soil type (e.g., 'Advice for Tomato in Sandy Loam'):", is_user=False)
        self.awaiting_advisory = True

    def faq_action(self, instance):
        if FAQ:
            self.add_bubble("Please enter your question or keyword for FAQ:", is_user=False)
            self.awaiting_faq = True
        else:
            self.add_bubble("FAQ module not available.", is_user=False)

    def weather_action(self, instance):
        if WeatherEstimator:
            self.add_bubble("Please enter your location for weather estimation:", is_user=False)
            self.awaiting_weather = True
        else:
            self.add_bubble("Weather module not available.", is_user=False)

    def calendar_action(self, instance):
        if CropCalendar:
            self.add_bubble("Please enter the crop name for calendar:", is_user=False)
            self.awaiting_calendar = True
        else:
            self.add_bubble("Calendar module not available.", is_user=False)

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
            if self.awaiting_advisory:
                crop, soil = self.parse_crop_soil(user_text)
                if crop:
                    if get_crop_advice:
                        advice = get_crop_advice(crop, soil)
                        self.add_bubble(advice, is_user=False)
                    else:
                        self.add_bubble("Advisory module not available.", is_user=False)
                else:
                    self.add_bubble("Could not detect crop. Please try again.", is_user=False)
                self.awaiting_advisory = False

            elif self.awaiting_faq:
                if FAQ:
                    faq = FAQ()
                    results = faq.search(user_text)
                    if results:
                        for item in results:
                            self.add_bubble(f"Q: {item['question']}\nA: {item['answer']}", is_user=False)
                    else:
                        self.add_bubble("No matching FAQ found.", is_user=False)
                else:
                    self.add_bubble("FAQ module not available.", is_user=False)
                self.awaiting_faq = False

            elif self.awaiting_weather:
                if WeatherEstimator:
                    estimator = WeatherEstimator()
                    try:
                        weather = estimator.estimate(user_text)
                    except TypeError:
                        weather = estimator.estimate()
                    self.add_bubble(f"Weather Estimation:\n{weather}", is_user=False)
                else:
                    self.add_bubble("Weather module not available.", is_user=False)
                self.awaiting_weather = False

            elif self.awaiting_calendar:
                if CropCalendar:
                    calendar = CropCalendar()
                    schedule = calendar.get_schedule(user_text)
                    self.add_bubble(f"Crop Calendar for {user_text.title()}:\n{schedule}", is_user=False)
                else:
                    self.add_bubble("Calendar module not available.", is_user=False)
                self.awaiting_calendar = False

            else:
                agent_response = self.get_agent_response(user_text)
                self.add_bubble(agent_response, is_user=False)
        except Exception as e:
            self.add_bubble(f"Error: {str(e)}", is_user=False)
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