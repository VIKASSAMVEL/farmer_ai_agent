from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle

class IOSButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0)
        self.color = (1, 1, 1, 1)
        self.font_size = 16
        self.size_hint = (None, None)
        self.size = (120, 40)
        self.radius = [20]
        self.bind(pos=self.update_canvas, size=self.update_canvas)  # type: ignore
        with self.canvas.before:  # type: ignore
            Color(0.1, 0.1, 0.1, 1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=self.radius)

    def update_canvas(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
# Kivy Chat-like UI for Farmer Agent (ChatGPT style)
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout

class ChatBubble(Label):
    def __init__(self, text, is_user=False, **kwargs):
        super().__init__(**kwargs)
        self.text = text

# ...existing imports...
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout

# Backend imports
import sys
sys.path.append('..')
try:
    from advisory.advisor import get_crop_advice
    from data.faq import FAQ
    from data.weather import WeatherEstimator
    from data.crop_calendar import CropCalendar
except Exception:
    get_crop_advice = None
    FAQ = None
    WeatherEstimator = None
    CropCalendar = None


class ChatScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        # Feature selection area - horizontal, left-aligned, iOS style
        self.feature_box = BoxLayout(orientation='horizontal', size_hint=(1, 0.12), spacing=10, padding=[10,10,10,10])
        self.feature_btns = []
        features = [
            ('Input', self.input_action),
            ('Crop Advisory', self.advisory_action),
            ('Calendar', self.calendar_action),
            ('FAQ', self.faq_action),
            ('Weather', self.weather_action),
            ('Analytics', self.analytics_action),
            ('Exit', self.exit_action)
        ]
        for label, handler in features:
            btn = IOSButton(text=label)
            btn.bind(on_press=handler)  # type: ignore
            self.feature_btns.append(btn)
            self.feature_box.add_widget(btn)
        self.add_widget(self.feature_box)

        # Chat history in center
        self.chat_history = GridLayout(cols=1, spacing=10, size_hint_y=None, padding=[10,0,10,0])
        self.chat_history.bind(minimum_height=self.chat_history.setter('height'))  # type: ignore
        self.scroll = ScrollView(size_hint=(1, 0.73))
        self.scroll.add_widget(self.chat_history)
        self.add_widget(self.scroll)

        # Input field at bottom
        self.input_box = BoxLayout(size_hint=(1, 0.15), padding=[10,10,10,10], spacing=10)
        self.text_input = TextInput(hint_text='Type your message...', multiline=False, size_hint=(0.8, 1), font_size=16, background_color=(0.15,0.15,0.15,1), foreground_color=(1,1,1,1), padding=[10,10,10,10])
        self.send_btn = Button(text='Send', size_hint=(0.2, 1), background_normal='', background_color=(0.1,0.1,0.1,1), color=(1,1,1,1), font_size=16, border=(20,20,20,20))
        self.send_btn.bind(on_press=self.send_message)  # type: ignore
        self.input_box.add_widget(self.text_input)
        self.input_box.add_widget(self.send_btn)
        self.add_widget(self.input_box)

    def _make_gradient_rect(self, btn):
        from kivy.graphics import Color, RoundedRectangle
        # Matte black with subtle gradient
        instr = []
        instr.append(Color(0.1, 0.1, 0.1, 1))
        instr.append(RoundedRectangle(pos=btn.pos, size=btn.size, radius=[20]))
        return instr

    # Feature button handlers
    def input_action(self, instance):
        self.add_bubble("Input Modes: Type your message below or use chat for voice/image/text.", is_user=False)

    def advisory_action(self, instance):
        # Prompt user for crop and soil
        self.add_bubble("Please enter your crop and soil type (e.g., 'Advice for Tomato in Sandy Loam'):", is_user=False)
        # When user sends a message, parse and call backend
        self.awaiting_advisory = True

    def send_message(self, instance):
        user_text = self.text_input.text.strip()
        if user_text:
            self.add_bubble(user_text, is_user=True)
            try:
                # If awaiting advisory, parse and call backend
                if hasattr(self, 'awaiting_advisory') and self.awaiting_advisory:
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
                else:
                    agent_response = self.get_agent_response(user_text)
                    self.add_bubble(agent_response, is_user=False)
            except Exception as e:
                self.add_bubble(f"Error: {str(e)}", is_user=False)
            self.text_input.text = ''

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




    def analytics_action(self, instance):
        self.add_bubble("Analytics feature coming soon!", is_user=False)

    def exit_action(self, instance):
        self.add_bubble("Goodbye! Close the window to exit.", is_user=False)

    def send_message(self, instance):
        user_text = self.text_input.text.strip()
        if user_text:
            self.add_bubble(user_text, is_user=True)
            try:
                agent_response = self.get_agent_response(user_text)
            except Exception as e:
                agent_response = f"Error: {str(e)}"
            self.add_bubble(agent_response, is_user=False)
            self.text_input.text = ''

    def add_bubble(self, text, is_user=False):
        bubble = ChatBubble(text, is_user=is_user)
        self.chat_history.add_widget(bubble)
        self.scroll.scroll_y = 0

    def get_agent_response(self, user_text):
        # Simple intent parsing
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
                return f"FAQ Results:\n" + str(results)
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

    # Quick action handlers
    def faq_action(self, instance):
        try:
            if FAQ:
                faq = FAQ()
                results = faq.get_all()
                self.add_bubble(f"FAQ Results:\n{results}", is_user=False)
            else:
                self.add_bubble("FAQ module not available.", is_user=False)
        except Exception as e:
            self.add_bubble(f"Error: {str(e)}", is_user=False)

    def weather_action(self, instance):
        try:
            if WeatherEstimator:
                estimator = WeatherEstimator()
                weather = estimator.estimate()
                self.add_bubble(f"Weather Estimation:\n{weather}", is_user=False)
            else:
                self.add_bubble("Weather module not available.", is_user=False)
        except Exception as e:
            self.add_bubble(f"Error: {str(e)}", is_user=False)
        try:
            if FAQ:
                self.add_bubble("Please enter your question or keyword for FAQ:", is_user=False)
                self.awaiting_faq = True
            else:
                self.add_bubble("FAQ module not available.", is_user=False)
        except Exception as e:
            self.add_bubble(f"Error: {str(e)}", is_user=False)
        except Exception as e:
            self.add_bubble(f"Error: {str(e)}", is_user=False)

class FarmerAgentApp(App):
    def build(self):
        return ChatScreen()

if __name__ == '__main__':
    FarmerAgentApp().run()
