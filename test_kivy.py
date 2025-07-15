import os
import logging
import traceback
import json
import threading
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, RoundedRectangle
from kivy.core.window import Window
from kivy.resources import resource_find
from kivy.clock import Clock
from kivy.uix.dropdown import DropDown
from kivy.uix.filechooser import FileChooserIconView

# Configure logging
logging.basicConfig(
    filename='kivy_chat_log.txt',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s',
    encoding='utf-8'
)

# Backend imports with error handling
try:
    from farmer_agent.advisory.advisor import get_crop_advice
    from farmer_agent.data.faq import FAQ
    from farmer_agent.data.weather import WeatherEstimator
    from farmer_agent.data.crop_calendar import CropCalendar, Reminders
    from farmer_agent.nlp.stt import recognize_speech, STT
    from farmer_agent.nlp.tts import speak, list_voices
    from farmer_agent.nlp.translate import OfflineTranslator
    from farmer_agent.nlp.cv import PlantIdentifier
    from farmer_agent.utils.file_utils import load_json
    from farmer_agent.data.user_profile import UserManager
    from farmer_agent.data.analytics import Analytics
    from farmer_agent.utils.env_loader import load_env_local
except ImportError as e:
    logging.error(f"Backend import error: {str(e)}")
    get_crop_advice = FAQ = WeatherEstimator = CropCalendar = Reminders = recognize_speech = STT = speak = list_voices = OfflineTranslator = PlantIdentifier = load_json = UserManager = Analytics = load_env_local = None

class ChatBubble(BoxLayout):
    def __init__(self, text, is_user=False, **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=None, padding=[10, 5, 10, 5], **kwargs)
        timestamp = datetime.now().strftime('%H:%M')
        self.bubble_color = (0.2, 0.6, 0.2, 1) if is_user else (0.9, 0.9, 0.9, 1)
        self.label = Label(
            text=text,
            size_hint_x=0.85,
            halign='right' if is_user else 'left',
            valign='top',
            color=(1, 1, 1, 1) if is_user else (0, 0, 0, 1),
            text_size=(Window.width * 0.7, None),
            markup=True
        )
        self.label.bind(texture_size=self._update_height)  # type: ignore
        self.timestamp_label = Label(
            text=timestamp,
            size_hint_x=0.15,
            font_size=12,
            color=(0.5, 0.5, 0.5, 1),
            halign='right',
            valign='bottom'
        )
        self.add_widget(self.label)
        self.add_widget(self.timestamp_label)
        with self.canvas.before:  # type: ignore
            Color(0, 0, 0, 0.18)
            self.shadow_rect = RoundedRectangle(radius=[17], pos=(self.pos[0]+2, self.pos[1]-2), size=(self.size[0], self.size[1]))
            self.bg_color_instruction = Color(*self.bubble_color)
            self.bg_rect = RoundedRectangle(radius=[15], pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg_rect, size=self._update_bg_rect)  # type: ignore

    def _update_bg_rect(self, *args):
        if hasattr(self, 'shadow_rect'):
            self.shadow_rect.pos = (self.pos[0]+2, self.pos[1]-2)
            self.shadow_rect.size = (self.size[0], self.size[1])
        if hasattr(self, 'bg_rect'):
            self.bg_rect.pos = self.pos
            self.bg_rect.size = self.size

    def _update_height(self, *args):
        min_height = 40
        padding = 24
        self.label.height = max(self.label.texture_size[1] + padding, min_height)
        self.height = self.label.height + 10

def show_debug_popup(error_msg):
    content = BoxLayout(orientation='vertical')
    label = Label(text=error_msg, size_hint_y=None, height=400, font_name='DejaVuSans')
    btn = Button(text='Close', size_hint_y=None, height=40)
    content.add_widget(label)
    content.add_widget(btn)
    popup = Popup(title='Debugger - Error Traceback', content=content, size_hint=(0.9, 0.7))
    btn.bind(on_release=popup.dismiss)  # type: ignore
    popup.open()

class ChatScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.state = {"mode": None, "context": {}}
        def get_scaled(val):
            return int(val * Window.width / 800)

        # --- Top bar with app title and language dropdown ---
        top_bar = BoxLayout(size_hint=(1, 0.08), padding=[0, get_scaled(8), 0, get_scaled(8)])
        header_label = Label(text='Farmer AI Agent', font_size=get_scaled(28), bold=True, color=(0.2, 0.6, 0.2, 1))
        # Language dropdown
        self.language_dropdown = DropDown()
        self.language_options = [
            ("English", "en"), ("Hindi", "hi"), ("Tamil", "ta"), ("Telugu", "te"), ("Kannada", "kn"), ("Malayalam", "ml")
        ]
        self.language_btn = Button(text="🌐 Language", size_hint=(None, 1), width=160)
        for lang_name, lang_code in self.language_options:
            btn = Button(text=lang_name, size_hint_y=None, height=44)
            btn.bind(on_release=lambda btn, code=lang_code: self.set_language(code))
            self.language_dropdown.add_widget(btn)
        self.language_btn.bind(on_release=self.language_dropdown.open)
        top_bar.add_widget(header_label)
        top_bar.add_widget(self.language_btn)
        self.add_widget(top_bar)

        # --- Mode dropdown (Advisory, Calendar, FAQ, Weather, Translate, Analytics) ---
        mode_bar = BoxLayout(size_hint=(1, 0.08), padding=[get_scaled(16), 0, get_scaled(16), 0])
        self.mode_dropdown = DropDown()
        self.mode_options = [
            ("Advisory", self.advisory_action),
            ("Calendar", self.calendar_action),
            ("FAQ", self.faq_action),
            ("Weather", self.weather_action),
            ("Translate", self.translate_action),
            ("Analytics", self.analytics_action)
        ]
        self.mode_btn = Button(text="Select Mode", size_hint=(None, 1), width=180)
        for mode_name, mode_func in self.mode_options:
            btn = Button(text=mode_name, size_hint_y=None, height=44)
            btn.bind(on_release=lambda btn, func=mode_func: self.select_mode(func))
            self.mode_dropdown.add_widget(btn)
        self.mode_btn.bind(on_release=self.mode_dropdown.open)
        mode_bar.add_widget(self.mode_btn)
        self.add_widget(mode_bar)

        # --- Chat history area (unchanged) ---
        chat_area = BoxLayout(size_hint=(1, 0.62), padding=[get_scaled(16), get_scaled(8), get_scaled(16), get_scaled(8)])
        self.chat_history = GridLayout(cols=1, spacing=get_scaled(14), size_hint_y=None)
        self.chat_history.bind(minimum_height=self.chat_history.setter('height'))  # type: ignore
        self.scroll = ScrollView(size_hint=(1, 1))
        self.scroll.add_widget(self.chat_history)
        chat_area.add_widget(self.scroll)
        self.add_widget(chat_area)
        # Divider
        class Divider(BoxLayout):
            def __init__(self, **kwargs):
                super().__init__(size_hint=(1, None), height=2, **kwargs)
                with self.canvas:  # type: ignore
                    Color(0.8, 0.8, 0.8, 1)
                    from kivy.graphics import Rectangle
                    self.rect = Rectangle(pos=self.pos, size=(self.width, 2))
                self.bind(pos=self._update_rect, size=self._update_rect)  # type: ignore
            def _update_rect(self, *args):
                self.rect.pos = self.pos
                self.rect.size = (self.width, 2)
        self.add_widget(Divider())
        # --- Input dropdown (Text, Image) ---
        input_bar = BoxLayout(size_hint=(1, 0.12), padding=[get_scaled(16), get_scaled(8), get_scaled(16), get_scaled(8)], spacing=get_scaled(12))
        self.input_dropdown = DropDown()
        self.input_options = [
            ("Text", self.set_input_text),
            ("Image", self.set_input_image)
        ]
        self.input_btn = Button(text="Input Type", size_hint=(None, 1), width=140)
        for input_name, input_func in self.input_options:
            btn = Button(text=input_name, size_hint_y=None, height=44)
            btn.bind(on_release=lambda btn, func=input_func: func())
            self.input_dropdown.add_widget(btn)
        self.input_btn.bind(on_release=self.input_dropdown.open)
        input_bar.add_widget(self.input_btn)
        # Add text input and send button as before
        class RoundedInput(TextInput):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.background_color = (0, 0, 0, 0)
                self.hint_text = 'Type your message...'
                self.font_size = get_scaled(18)
                self.padding = [get_scaled(16), get_scaled(12), get_scaled(16), get_scaled(12)]
                self.foreground_color = (0, 0, 0, 1)  # Black text for visibility
                with self.canvas.before:  # type: ignore
                    Color(0.95, 0.95, 0.95, 1)
                    self.bg_rect = RoundedRectangle(radius=[get_scaled(18)], pos=self.pos, size=self.size)
                self.bind(pos=self._update_bg, size=self._update_bg)  # type: ignore
            def _update_bg(self, *args):
                self.bg_rect.pos = self.pos
                self.bg_rect.size = self.size
        self.text_input = RoundedInput(size_hint=(0.8, 1), multiline=False)
        class RoundedButton(Button):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.background_normal = ''
                self.background_color = (0.2, 0.6, 0.2, 1)
                self.color = (1, 1, 1, 1)
                self.font_size = get_scaled(18)
                with self.canvas.before:  # type: ignore
                    Color(0.2, 0.6, 0.2, 1)
                    self.bg_rect = RoundedRectangle(radius=[get_scaled(18)], pos=self.pos, size=self.size)
                self.bind(pos=self._update_bg, size=self._update_bg)
                self.bind(on_enter=lambda x: setattr(self, 'background_color', (0.3, 0.7, 0.3, 1)))  # type: ignore
                self.bind(on_leave=lambda x: setattr(self, 'background_color', (0.2, 0.6, 0.2, 1)))  # type: ignore
            def _update_bg(self, *args):
                self.bg_rect.pos = self.pos
                self.bg_rect.size = self.size
        send_btn = RoundedButton(text='Send', size_hint=(0.2, 1))
        send_btn.bind(on_release=self.send_message)  # type: ignore
        self.mic_btn = None  # Placeholder for mic button
        self.is_recording = False  # Track mic recording state
        input_bar.add_widget(self.text_input)
        input_bar.add_widget(send_btn)
        self.add_widget(input_bar)

        # --- Remove old feature buttons bar ---
        # ...existing code...

        # --- Footer (unchanged) ---
        footer = BoxLayout(size_hint=(1, 0.05), padding=[0, get_scaled(4), 0, get_scaled(4)])
        footer_label = Label(text='© 2025 Farmer AI Agent | Powered by Open Source | Accessible Design', font_size=get_scaled(14), color=(0.2, 0.6, 0.2, 1))
        footer.add_widget(footer_label)
        self.add_widget(footer)
        # Initialize UserManager
        if load_env_local:
            try:
                load_env_local()
            except Exception as e:
                logging.error(f"load_env_local error: {str(e)}")
                self.add_bubble(f"Environment setup error: {str(e)}", is_user=False)
        self.user_manager = None
        try:
            if UserManager:
                self.user_manager = UserManager()
                users = self.user_manager.list_users()
                if users:
                    self.user_manager.switch_user(users[0])
                else:
                    self.user_manager.add_user('default')
                    self.user_manager.switch_user('default')
            else:
                self.add_bubble("User profile system unavailable. Some features may be limited.", is_user=False)
        except Exception as e:
            logging.error(f"UserManager init error: {str(e)}")
            self.add_bubble(f"User profile error: {str(e)}", is_user=False)

    def add_bubble(self, text, is_user=False):
        try:
            formatted_text = text
            if not is_user:
                try:
                    if isinstance(text, str) and text.strip().startswith('{') and text.strip().endswith('}'):
                        obj = json.loads(text)
                        formatted_text = json.dumps(obj, indent=2, ensure_ascii=False)
                    elif isinstance(text, str) and text.strip().startswith('[') and text.strip().endswith(']'):
                        obj = json.loads(text)
                        if isinstance(obj, list):
                            formatted_text = "\n".join([f"• {item}" for item in obj])
                except Exception:
                    pass
            bubble = ChatBubble(formatted_text, is_user=is_user)
            self.chat_history.add_widget(bubble)
            self.chat_history.height = self.chat_history.minimum_height
            self.scroll.scroll_to(bubble, padding=10, animate=True)
            # Log message
            prefix = 'USER' if is_user else 'AGENT'
            logging.info(f"[{prefix}] {text}")
            # Prevent duplicate 'User history cleared.' logs
            if text == 'User history cleared.':
                try:
                    with open('kivy_chat_log.txt', 'r', encoding='utf-8') as logf:
                        lines = logf.readlines()
                        if lines and 'User history cleared.' in lines[-1]:
                            last_time = lines[-1].split(' ')[0]
                            last_dt = datetime.strptime(last_time, '%Y-%m-%d')
                            if (datetime.now() - last_dt).total_seconds() < 2:
                                return
                except Exception:
                    pass
        except Exception as e:
            logging.error(f"add_bubble error: {str(e)}")
            self.add_bubble(f"Error displaying message: {str(e)}", is_user=False)

    def select_mode(self, func):
        self.mode_dropdown.dismiss()
        func(None)

    def set_input_text(self):
        self.input_dropdown.dismiss()
        self.text_input.disabled = False
        self.text_input.text = ''
        self.state['input_type'] = 'text'

    def set_input_image(self):
        self.input_dropdown.dismiss()
        self.text_input.disabled = True
        # Open file chooser popup for image selection
        filechooser = FileChooserIconView(filters=['*.png', '*.jpg', '*.jpeg', '*.bmp'], path='~')
        popup = Popup(title='Select Image', content=filechooser, size_hint=(0.9, 0.9))
        def on_selection(instance, selection):
            if selection:
                self.state['selected_image'] = selection[0]
                popup.dismiss()
                self.handle_image_input(selection[0])
        filechooser.bind(selection=on_selection)
        popup.open()

    def handle_image_input(self, image_path):
        # This function should handle image input for the current mode
        self.add_bubble(f"Image selected: {image_path}", is_user=True)
        # You can add logic to process the image as per the selected mode

    def set_language(self, lang_code):
        self.language_dropdown.dismiss()
        self.state['language'] = lang_code
        # TODO: Call translate function for UI, responses, and speech
        self.add_bubble(f"Language set to: {lang_code}", is_user=False)

    def input_action(self, instance):
        if recognize_speech:
            self.add_bubble("Input Modes: 1. Voice (mic) 2. Audio File 3. Text 4. Image", is_user=False)
            self.state["mode"] = "input"
        else:
            self.add_bubble("Voice input not available.", is_user=False)

    def advisory_action(self, instance):
        if not get_crop_advice:
            self.add_bubble("Advisory module not available.", is_user=False)
            return
        crop_list = ["Tomato", "Rice", "Wheat", "Maize", "Potato", "Onion", "Cotton", "Sugarcane"]
        self.state["mode"] = "advisory"
        self.state["context"]["crop_list"] = crop_list
        self.add_bubble("Select your crop for advisory:", is_user=False)
        crop_spinner = Spinner(
            text="Select Crop",
            values=crop_list,
            size_hint=(None, None),
            size=(200, 44),
            pos_hint={'center_x': 0.5}
        )
        def on_crop_select(spinner, text):
            self.text_input.text = text
            self.state["mode"] = "advisory_crop"
            self.chat_history.remove_widget(crop_spinner)
        crop_spinner.bind(text=on_crop_select)  # type: ignore
        self.chat_history.add_widget(crop_spinner)

    def calendar_action(self, instance):
        try:
            if not CropCalendar or not Reminders:
                self.add_bubble("Calendar module not available.", is_user=False)
                return
            self.calendar = CropCalendar()
            self.reminders = Reminders()
            self.state["mode"] = "calendar_option"
            self.add_bubble("Calendar options: 1. View crop schedule 2. List crops 3. Add reminder 4. Add recurring reminder 5. Delete reminder 6. Next activity\nEnter option number:", is_user=False)
        except Exception as e:
            logging.error(f"calendar_action error: {str(e)}")
            self.add_bubble(f"Calendar module error: {str(e)}", is_user=False)

    def faq_action(self, instance):
        if not FAQ:
            self.add_bubble("FAQ module not available.", is_user=False)
            return
        spinner = Spinner(size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.chat_history.add_widget(spinner)
        self.text_input.disabled = True
        def run_faq():
            result_bubbles = []
            try:
                self.state["mode"] = "faq"
                result_bubbles.append(("Please enter your question or keyword for FAQ:", False))
            except Exception as e:
                result_bubbles.append((f"FAQ error: {str(e)}", False))
            finally:
                Clock.schedule_once(lambda dt: self._update_ui(spinner, result_bubbles), 0)
        threading.Thread(target=run_faq).start()

    def weather_action(self, instance):
        if not WeatherEstimator:
            self.add_bubble("Weather module not available.", is_user=False)
            return
        spinner = Spinner(size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.chat_history.add_widget(spinner)
        self.text_input.disabled = True
        def run_weather():
            result_bubbles = []
            try:
                estimator = WeatherEstimator()
                location = estimator.get_current_location()
                if location:
                    result_bubbles.append((f"Detected location: {location}", False))
                    weekly = estimator.fetch_weekly_forecast(location)
                    if weekly:
                        result_bubbles.append((f"7-Day Weather Forecast for {location}:", False))
                        result_bubbles.append((json.dumps(weekly, indent=2, ensure_ascii=False), False))
                        tips = estimator.get_llm_weather_tips(weekly)
                        result_bubbles.append(("LLM Tips for Farmers:", False))
                        result_bubbles.append((tips, False))
                    else:
                        result_bubbles.append(("Could not fetch weekly forecast. Check API key or location.", False))
                else:
                    result_bubbles.append(("Could not detect location.", False))
            except Exception as e:
                logging.error(f"weather_action error: {str(e)}")
                result_bubbles.append((f"Weather error: {str(e)}", False))
            finally:
                Clock.schedule_once(lambda dt: self._update_ui(spinner, result_bubbles), 0)
        threading.Thread(target=run_weather).start()

    def translate_action(self, instance):
        if not OfflineTranslator:
            self.add_bubble("Translation module not available.", is_user=False)
            return
        spinner = Spinner(size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.chat_history.add_widget(spinner)
        self.text_input.disabled = True
        def run_translate():
            result_bubbles = []
            try:
                self.state["mode"] = "translate_text"
                result_bubbles.append(("Enter text to translate from English:", False))
            except Exception as e:
                logging.error(f"translate_action error: {str(e)}")
                result_bubbles.append((f"Translate error: {str(e)}", False))
            finally:
                Clock.schedule_once(lambda dt: self._update_ui(spinner, result_bubbles), 0)
        threading.Thread(target=run_translate).start()

    def analytics_action(self, instance):
        if not Analytics:
            self.add_bubble("Analytics module not available.", is_user=False)
            return
        spinner = Spinner(size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.chat_history.add_widget(spinner)
        self.text_input.disabled = True
        def run_analytics():
            result_bubbles = []
            try:
                analytics = Analytics()
                result_bubbles.append(("User Activity Summary:", False))
                result_bubbles.append((json.dumps(analytics.user_activity_summary('default'), indent=2, ensure_ascii=False), False))
                result_bubbles.append(("Crop Trends:", False))
                result_bubbles.append((json.dumps(analytics.crop_trends(), indent=2, ensure_ascii=False), False))
            except Exception as e:
                logging.error(f"analytics_action error: {str(e)}")
                result_bubbles.append((f"Error in analytics: {str(e)}", False))
            finally:
                Clock.schedule_once(lambda dt: self._update_ui(spinner, result_bubbles), 0)
        threading.Thread(target=run_analytics).start()

    def tts_voices_action(self, instance):
        if not list_voices:
            self.add_bubble("TTS Voices module not available.", is_user=False)
            return
        spinner = Spinner(size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.chat_history.add_widget(spinner)
        self.text_input.disabled = True
        def run_tts_voices():
            result_bubbles = []
            try:
                import io
                import contextlib
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    list_voices()
                voices = buf.getvalue()
                result_bubbles.append(("Available TTS Voices:", False))
                result_bubbles.append((voices, False))
            except Exception as e:
                logging.error(f"tts_voices_action error: {str(e)}")
                result_bubbles.append((f"TTS Voices error: {str(e)}", False))
            finally:
                Clock.schedule_once(lambda dt: self._update_ui(spinner, result_bubbles), 0)
        threading.Thread(target=run_tts_voices).start()

    def clear_history_action(self, instance):
        try:
            if self.user_manager and self.user_manager.current_user:
                self.user_manager.current_user.clear_history()
                self.add_bubble("User history cleared.", is_user=False)
            else:
                self.add_bubble("User profile not loaded.", is_user=False)
        except Exception as e:
            logging.error(f"clear_history_action error: {str(e)}")
            show_debug_popup(traceback.format_exc())

    def exit_action(self, instance):
        self.add_bubble("Goodbye! Close the window to exit.", is_user=False)

    def _update_ui(self, spinner, result_bubbles):
        self.chat_history.remove_widget(spinner)
        self.text_input.disabled = False
        for text, is_user in result_bubbles:
            self.add_bubble(text, is_user=is_user)

    def send_message(self, instance):
        user_text = self.text_input.text.strip()
        if not user_text:
            return
        self.add_bubble(user_text, is_user=True)
        try:
            # Input validation
            if self.state.get("mode") == "advisory_crop":
                crop_list = self.state["context"].get("crop_list", [])
                if user_text not in crop_list:
                    self.add_bubble(f"Invalid crop name. Please select from: {', '.join(crop_list)}", is_user=False)
                    return
            if self.state.get("mode") == "weather_date":
                try:
                    if user_text:
                        datetime.strptime(user_text, "%Y-%m-%d")
                except ValueError:
                    self.add_bubble("Invalid date format. Please use YYYY-MM-DD.", is_user=False)
                    return
            # Handle state-based input
            if self.state.get("mode") == "calendar_option":
                self.handle_calendar_option(user_text)
                self.state["mode"] = None
            elif self.state.get("mode") == "calendar_crop":
                crop = user_text.strip()
                self.state["context"]["last_calendar_crop"] = crop
                self.add_bubble("Crop Calendar:", is_user=False)
                if self.calendar:
                    self.add_bubble(json.dumps(self.calendar.get_schedule(crop), indent=2, ensure_ascii=False), is_user=False)
                self.add_bubble("Reminders:", is_user=False)
                if self.reminders:
                    self.add_bubble(json.dumps(self.reminders.get_upcoming(), indent=2, ensure_ascii=False), is_user=False)
                self.state["mode"] = None
            elif self.state.get("mode") == "reminder_crop":
                self.state["context"]["reminder_crop"] = user_text.strip()
                self.add_bubble("Activity:", is_user=False)
                self.state["mode"] = "reminder_activity"
            elif self.state.get("mode") == "reminder_activity":
                self.state["context"]["reminder_activity"] = user_text.strip()
                self.add_bubble("Days from now:", is_user=False)
                self.state["mode"] = "reminder_days"
            elif self.state.get("mode") == "reminder_days":
                try:
                    days = int(user_text.strip())
                    if self.reminders:
                        self.reminders.add_reminder(self.state["context"]["reminder_crop"], self.state["context"]["reminder_activity"], days)
                        self.add_bubble("Reminder added.", is_user=False)
                except ValueError:
                    self.add_bubble("Error: Invalid number of days.", is_user=False)
                self.state["mode"] = None
            elif self.state.get("mode") == "recurring_crop":
                self.state["context"]["recurring_crop"] = user_text.strip()
                self.add_bubble("Activity:", is_user=False)
                self.state["mode"] = "recurring_activity"
            elif self.state.get("mode") == "recurring_activity":
                self.state["context"]["recurring_activity"] = user_text.strip()
                self.add_bubble("Start in how many days?:", is_user=False)
                self.state["mode"] = "recurring_start"
            elif self.state.get("mode") == "recurring_start":
                try:
                    self.state["context"]["recurring_start"] = int(user_text.strip())
                    self.add_bubble("Interval (days):", is_user=False)
                    self.state["mode"] = "recurring_interval"
                except ValueError:
                    self.add_bubble("Error: Invalid number of days.", is_user=False)
                self.state["mode"] = None
            elif self.state.get("mode") == "recurring_interval":
                try:
                    self.state["context"]["recurring_interval"] = int(user_text.strip())
                    self.add_bubble("Occurrences:", is_user=False)
                    self.state["mode"] = "recurring_occurrences"
                except ValueError:
                    self.add_bubble("Error: Invalid interval.", is_user=False)
                self.state["mode"] = None
            elif self.state.get("mode") == "recurring_occurrences":
                try:
                    occurrences = int(user_text.strip())
                    if self.reminders:
                        self.reminders.add_recurring_reminder(
                            self.state["context"]["recurring_crop"],
                            self.state["context"]["recurring_activity"],
                            self.state["context"]["recurring_start"],
                            self.state["context"]["recurring_interval"],
                            occurrences
                        )
                        self.add_bubble("Recurring reminder(s) added.", is_user=False)
                except ValueError:
                    self.add_bubble("Error: Invalid number of occurrences.", is_user=False)
                self.state["mode"] = None
            elif self.state.get("mode") == "delete_crop":
                crop = user_text.strip()
                if self.reminders:
                    self.reminders.delete_reminder(crop)
                    self.add_bubble(f"All reminders for {crop} deleted.", is_user=False)
                self.state["mode"] = None
            elif self.state.get("mode") == "next_activity_crop":
                crop = user_text.strip()
                next_act = self.calendar.next_activity(crop) if self.calendar else None
                if next_act:
                    self.add_bubble(f"Next activity for {crop}: {next_act['activity']} on {next_act['date']}", is_user=False)
                else:
                    self.add_bubble(f"No upcoming activities for {crop}.", is_user=False)
                self.state["mode"] = None
            elif self.state.get("mode") == "advisory_crop":
                spinner = Spinner(size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.5, 'center_y': 0.5})
                self.chat_history.add_widget(spinner)
                self.text_input.disabled = True
                def run_advisory():
                    result_bubbles = []
                    try:
                        crop = user_text.strip()
                        advice = get_crop_advice(crop)
                        result_bubbles.append(("=== STRUCTURED ADVISORY ===", False))
                        result_bubbles.append((json.dumps(advice, indent=2, ensure_ascii=False), False))
                        result_bubbles.append(("=== FORMATTED ADVISORY ===", False))
                        result_bubbles.append((advice['formatted'], False))
                        self.state["context"]["last_advisory"] = advice
                        self.state["context"]["last_advisory_crop"] = crop
                        self.state["mode"] = "advisory_feedback"
                        result_bubbles.append(("Was this advice helpful? (y/n):", False))
                    except Exception as e:
                        logging.error(f"advisory_action error: {str(e)}")
                        result_bubbles.append((f"Error: {str(e)}", False))
                    finally:
                        Clock.schedule_once(lambda dt: self._update_ui(spinner, result_bubbles), 0)
                threading.Thread(target=run_advisory).start()
            elif self.state.get("mode") == "advisory_feedback":
                feedback = user_text.strip().lower()
                feedback_val = 'positive' if feedback == 'y' else ('negative' if feedback == 'n' else None)
                if feedback_val and "last_advisory" in self.state["context"]:
                    self.state["context"]["last_advisory"]["feedback"] = feedback_val
                    if self.user_manager and self.user_manager.current_user:
                        try:
                            self.user_manager.current_user.add_query(
                                f"{self.state['context']['last_advisory_crop']}, None",
                                self.state["context"]["last_advisory"]
                            )
                        except Exception as e:
                            logging.error(f"User profile save error: {str(e)}")
                self.add_bubble("Thank you for your feedback!", is_user=False)
                self.state["mode"] = None
            elif self.state.get("mode") == "faq":
                spinner = Spinner(size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.5, 'center_y': 0.5})
                self.chat_history.add_widget(spinner)
                self.text_input.disabled = True
                def run_faq():
                    result_bubbles = []
                    try:
                        faq = FAQ()
                        results = faq.search(user_text, use_llm=True)
                        if results:
                            answer = results[0].get('answer', '')
                            result_bubbles.append(("LLM FAQ Response:", False))
                            result_bubbles.append((answer, False))
                            if speak:
                                speak(answer)
                        else:
                            result_bubbles.append(("No response from LLM.", False))
                    except Exception as e:
                        logging.error(f"faq_action error: {str(e)}")
                        result_bubbles.append((f"FAQ error: {str(e)}", False))
                    finally:
                        Clock.schedule_once(lambda dt: self._update_ui(spinner, result_bubbles), 0)
                threading.Thread(target=run_faq).start()
            elif self.state.get("mode") == "translate_text":
                self.state["context"]["translate_text"] = user_text.strip()
                self.add_bubble("Enter target language code (hi=Hindi, ta=Tamil, te=Telugu, kn=Kannada, ml=Malayalam):", is_user=False)
                self.state["mode"] = "translate_lang"
            elif self.state.get("mode") == "translate_lang":
                tgt_lang = user_text.strip() or "hi"
                spinner = Spinner(size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.5, 'center_y': 0.5})
                self.chat_history.add_widget(spinner)
                self.text_input.disabled = True
                def run_translate():
                    result_bubbles = []
                    try:
                        translator = OfflineTranslator()
                        translated = translator.translate(self.state["context"]["translate_text"], "en", tgt_lang)
                        if translated.startswith("[Error]"):
                            result_bubbles.append((f"Translation failed: {translated}", False))
                        else:
                            result_bubbles.append((f"Translation: {translated}", False))
                    except Exception as e:
                        logging.error(f"translate_action error: {str(e)}")
                        result_bubbles.append((f"Translation error: {str(e)}", False))
                    finally:
                        Clock.schedule_once(lambda dt: self._update_ui(spinner, result_bubbles), 0)
                threading.Thread(target=run_translate).start()
                self.state["mode"] = None
            elif self.state.get("mode") == "input":
                mode = user_text.strip()
                if mode == "1":
                    if recognize_speech:
                        self.add_bubble("Please use the mic button to start and stop recording.", is_user=False)
                        self.state["mode"] = "stt_lang"
                        self.state["context"]["input_type"] = "mic"
                        # Add mic button if not present
                        if not self.mic_btn:
                            self.mic_btn = Button(text="🎤 Mic", size_hint=(None, None), size=(60, 44), background_color=(0.2, 0.6, 0.2, 1), color=(1, 1, 1, 1))
                            self.mic_btn.bind(on_release=self.start_mic_recording)
                            self.add_widget(self.mic_btn)
                    else:
                        self.add_bubble("Voice input not available.", is_user=False)
                        self.state["mode"] = None
                elif mode == "2":
                    self.add_bubble("Enter audio file path:", is_user=False)
                    self.state["mode"] = "audio_file"
                elif mode == "3":
                    self.add_bubble("Enter your request:", is_user=False)
                    self.state["mode"] = "text_input"
                elif mode == "4":
                    if PlantIdentifier:
                        self.add_bubble("Enter image path:", is_user=False)
                        self.state["mode"] = "image_path"
                    else:
                        self.add_bubble("Plant identification module not available.", is_user=False)
                        self.state["mode"] = None
                else:
                    self.add_bubble("Invalid input mode.", is_user=False)
                    self.state["mode"] = None
            elif self.state.get("mode") == "stt_lang" and self.state["context"].get("input_type") == "mic":
                self.add_bubble("Mic input not fully implemented. Please try another input mode.", is_user=False)
                self.state["mode"] = None
            elif self.state.get("mode") == "audio_file":
                file_path = user_text.strip()
                if not os.path.isfile(file_path):
                    self.add_bubble(f"Error: File {file_path} does not exist.", is_user=False)
                    self.state["mode"] = None
                    return
                self.state["context"]["audio_file_path"] = file_path
                self.add_bubble("Language code (default: auto):", is_user=False)
                self.state["mode"] = "audio_file_lang"
            elif self.state.get("mode") == "audio_file_lang":
                lang = user_text.strip() or "auto"
                spinner = Spinner(size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.5, 'center_y': 0.5})
                self.chat_history.add_widget(spinner)
                self.text_input.disabled = True
                def run_audio():
                    result_bubbles = []
                    try:
                        if STT:
                            stt = STT()
                            text = stt.transcribe_audio(self.state["context"]["audio_file_path"], language=lang)
                            result_bubbles.append((f"Transcribed Text: {text}", False))
                            if speak:
                                speak(text)
                        else:
                            result_bubbles.append(("Speech-to-text module not available.", False))
                    except Exception as e:
                        logging.error(f"audio_transcription error: {str(e)}")
                        result_bubbles.append((f"Error in audio transcription: {str(e)}", False))
                    finally:
                        Clock.schedule_once(lambda dt: self._update_ui(spinner, result_bubbles), 0)
                threading.Thread(target=run_audio).start()
                self.state["mode"] = None
            elif self.state.get("mode") == "text_input":
                text = user_text.strip()
                self.add_bubble(f"Text: {text}", is_user=False)
                if speak:
                    try:
                        speak(text)
                    except Exception as e:
                        logging.error(f"speak error: {str(e)}")
                        self.add_bubble(f"Error in text-to-speech: {str(e)}", is_user=False)
                self.state["mode"] = None
            elif self.state.get("mode") == "image_path":
                image_path = user_text.strip()
                if not os.path.isfile(image_path):
                    self.add_bubble(f"Error: File {image_path} does not exist.", is_user=False)
                    self.state["mode"] = None
                    return
                spinner = Spinner(size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.5, 'center_y': 0.5})
                self.chat_history.add_widget(spinner)
                self.text_input.disabled = True
                def run_image():
                    result_bubbles = []
                    try:
                        if PlantIdentifier:
                            identifier = PlantIdentifier()
                            plant_result = identifier.identify(image_path)
                            result_bubbles.append((f"Plant Identification Result: {plant_result}", False))
                            tips = identifier.get_llm_disease_tips(plant_result)
                            result_bubbles.append(("LLM Tips for Disease Solution/Medicine:", False))
                            result_bubbles.append((tips, False))
                        else:
                            result_bubbles.append(("Plant identification module not available.", False))
                    except Exception as e:
                        logging.error(f"image_identification error: {str(e)}")
                        result_bubbles.append((f"Error in plant identification: {str(e)}", False))
                    finally:
                        Clock.schedule_once(lambda dt: self._update_ui(spinner, result_bubbles), 0)
                threading.Thread(target=run_image).start()
                self.state["mode"] = None
            else:
                self.add_bubble("Sorry, I didn't understand. Try using a feature button.", is_user=False)
        except Exception as e:
            logging.error(f"send_message error: {str(e)}")
            self.add_bubble(f"Critical error: {str(e)}", is_user=False)
        self.text_input.text = ''

    def start_mic_recording(self, instance):
        """
        Toggles mic recording: starts on first click, stops and transcribes on second click.
        """
        try:
            if not recognize_speech:
                self.add_bubble("Voice input not available.", is_user=False)
                return
            if not self.is_recording:
                self.is_recording = True
                self.mic_btn.text = "⏹ Stop Mic"
                self.add_bubble("Recording... Please speak into the mic. Click again to stop.", is_user=False)
            else:
                self.is_recording = False
                self.mic_btn.text = "🎤 Mic"
                try:
                    # Only transcribe after stopping
                    text = recognize_speech(source='mic', lang='en')
                    # Ignore '[Mic Recording Started]' as valid transcription
                    if text and not str(text).startswith('[Error') and text.strip() and text.strip() != '[Mic Recording Started]':
                        self.add_bubble(f"Mic Input: {text}", is_user=True)
                        self.text_input.text = text
                        self.send_message(None)
                    else:
                        self.add_bubble("No speech detected. Please try again or check your microphone.", is_user=False)
                except Exception as e:
                    self.add_bubble(f"Mic error: {str(e)}. If using an audio file, please provide a valid file path. If using mic, ensure your microphone is enabled and working.", is_user=False)
        except Exception as e:
            self.add_bubble(f"Mic error: {str(e)}", is_user=False)

    def handle_calendar_option(self, user_text):
        option = user_text.strip()
        try:
            if not hasattr(self, 'calendar') or not hasattr(self, 'reminders'):
                self.calendar = CropCalendar()
                self.reminders = Reminders()
            if option == "1":
                self.add_bubble("Enter crop name:", is_user=False)
                self.state["mode"] = "calendar_crop"
            elif option == "2":
                crops = self.calendar.list_crops() if self.calendar else []
                self.add_bubble("Available crops: " + ", ".join(crops), is_user=False)
                self.state["mode"] = None
            elif option == "3":
                self.add_bubble("Enter crop name for reminder:", is_user=False)
                self.state["mode"] = "reminder_crop"
            elif option == "4":
                self.add_bubble("Enter crop name for recurring reminder:", is_user=False)
                self.state["mode"] = "recurring_crop"
            elif option == "5":
                self.add_bubble("Enter crop name to delete reminders:", is_user=False)
                self.state["mode"] = "delete_crop"
            elif option == "6":
                self.add_bubble("Enter crop name for next activity:", is_user=False)
                self.state["mode"] = "next_activity_crop"
            else:
                self.add_bubble("Invalid option.", is_user=False)
                self.state["mode"] = None
        except Exception as e:
            logging.error(f"handle_calendar_option error: {str(e)}")
            self.add_bubble(f"Calendar error: {str(e)}", is_user=False)
            self.state["mode"] = None

class FarmerAgentApp(App):
    def build(self):
        return ChatScreen()

if __name__ == "__main__":
    FarmerAgentApp().run()