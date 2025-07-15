import os
import logging
import traceback
import json
import threading
from datetime import datetime
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRectangleFlatButton, MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.filemanager import MDFileManager
from kivy.core.window import Window
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup

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

class ChatBubble(MDBoxLayout):
    def __init__(self, text, is_user=False, **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=None, padding=[16, 8, 16, 8], **kwargs)
        timestamp = datetime.now().strftime('%H:%M')
        bubble_color = (33/255, 194/255, 94/255, 1) if is_user else (27/255, 38/255, 59/255, 1)
        shadow_color = (0, 0, 0, 0.22)
        avatar_size = 40
        avatar_text = '🧑' if is_user else '🌾'  # Changed bot avatar
        avatar = MDLabel(text=avatar_text, font_style='H5', size_hint=(None, None), size=(avatar_size, avatar_size), theme_text_color='Custom', text_color=(0.2, 0.4, 1, 1))
        self.label = MDLabel(
            text=text,
            size_hint_x=0.75,
            halign='right' if is_user else 'left',
            valign='middle',
            theme_text_color='Custom',
            text_color=(1, 1, 1, 1) if is_user else (0.9, 0.9, 0.9, 1),  # Light text for better readability
            font_style='Body2',  # Slightly smaller font
            opacity=0
        )
        self.label.bind(texture_size=self._update_height)
        self.timestamp_label = MDLabel(
            text=timestamp,
            size_hint_x=0.15,
            font_style='Caption',
            theme_text_color='Custom',
            text_color=(0.2, 0.4, 1, 1),
            halign='left' if is_user else 'right',  # Timestamps on opposite sides
            valign='bottom'
        )
        # Layout: avatar | bubble | timestamp (user right, agent left)
        if is_user:
            self.add_widget(self.timestamp_label)
            self.add_widget(self.label)
            self.add_widget(avatar)
        else:
            self.add_widget(avatar)
            self.add_widget(self.label)
            self.add_widget(self.timestamp_label)
        # Fade-in animation for bubble
        from kivy.animation import Animation
        Animation(opacity=1, d=0.4, t='out_quad').start(self.label)

    def _update_height(self, *args):
        min_height = 48
        padding = 24 # Adjusted padding
        self.label.height = max(self.label.texture_size[1] + padding, min_height)
        self.height = self.label.height + 12

def show_debug_popup(error_msg):
    content = MDBoxLayout(orientation='vertical')
    label = MDLabel(text=error_msg, size_hint_y=None, height=400, font_name='DejaVuSans')
    btn = MDRectangleFlatButton(text='Close', size_hint_y=None, height=40)
    content.add_widget(label)
    content.add_widget(btn)
    popup = MDDialog(title='Debugger - Error Traceback', content=content, size_hint=(0.9, 0.7))
    btn.bind(on_release=popup.dismiss)  # type: ignore
    popup.open()

class ChatScreen(MDBoxLayout):
    @staticmethod
    def get_scaled(val):
        from kivy.core.window import Window
        return int(val * Window.width / 800)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.state = {"mode": None, "context": {}}
        # Professional dark background with rounded corners
        from kivy.graphics import Color, RoundedRectangle, BorderImage
        self.canvas.before.add(Color(0.07, 0.09, 0.13, 1))  # Dark background
        self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[32])  # Rounded rectangle shape
        # Add a subtle border
        self.canvas.before.add(self.bg_rect)
        self.bind(pos=self._update_bg, size=self._update_bg)

        # --- Mode bar ---
        mode_bar = MDBoxLayout(size_hint=(1, 0.09), padding=[ChatScreen.get_scaled(16), ChatScreen.get_scaled(8), ChatScreen.get_scaled(16), ChatScreen.get_scaled(8)], spacing=ChatScreen.get_scaled(16))
        self.mode_btn = MDRaisedButton(text="Select Mode", size_hint=(None, 1), width=140, md_bg_color=(0.13, 0.16, 0.22, 1), text_color=(0.8, 0.9, 1, 1), font_size=ChatScreen.get_scaled(18))
        self.mode_menu = MDDropdownMenu(
            caller=None,
            items=[
                {"text": "Input", "on_release": lambda: self.input_action(None)},
                {"text": "Advisory", "on_release": lambda: self.advisory_action(None)},
                {"text": "Calendar", "on_release": lambda: self.calendar_action(None)},
                {"text": "FAQ", "on_release": lambda: self.faq_action(None)},
                {"text": "Weather", "on_release": lambda: self.weather_action(None)},
                {"text": "Translate", "on_release": lambda: self.translate_action(None)},
                {"text": "Analytics", "on_release": lambda: self.analytics_action(None)},
                {"text": "TTS Voices", "on_release": lambda: self.tts_voices_action(None)},
                {"text": "Clear History", "on_release": lambda: self.clear_history_action(None)},
                {"text": "Exit", "on_release": lambda: self.exit_action(None)},
            ]
        )
        self.mode_menu.caller = self.mode_btn
        self.mode_btn.bind(on_release=lambda x: self.mode_menu.open())
        mode_bar.add_widget(self.mode_btn)  # Keep mode button
        self.language_btn = MDRaisedButton(text="🌐 Language", size_hint=(None, 1), width=140, md_bg_color=(0.13, 0.16, 0.22, 1), text_color=(0.8, 0.9, 1, 1), font_size=ChatScreen.get_scaled(18))
        self.language_dropdown = MDDropdownMenu(
            caller=None,
            items=[
                {"text": "English", "on_release": lambda: self.set_language('en')},
                {"text": "தமிழ்", "on_release": lambda: self.set_language('ta')},
                # Add more languages as needed, e.g., {"text": "हिन्दी", "on_release": lambda: self.set_language('hi')},
            ]
        )
        self.language_dropdown.caller = self.language_btn
        self.language_btn.bind(on_release=lambda x: self.language_dropdown.open())
        mode_bar.add_widget(self.language_btn)  # Keep language button
        self.add_widget(mode_bar)

        # --- Chat history area ---
        chat_area = MDBoxLayout(size_hint=(1, 0.62), padding=[ChatScreen.get_scaled(16), ChatScreen.get_scaled(8), ChatScreen.get_scaled(16), ChatScreen.get_scaled(8)])
        self.chat_history = MDGridLayout(cols=1, spacing=ChatScreen.get_scaled(14), size_hint_y=None)
        self.chat_history.bind(minimum_height=self.chat_history.setter('height'))  # type: ignore
        self.scroll = MDScrollView(size_hint=(1, 1))
        self.scroll.add_widget(self.chat_history)
        chat_area.add_widget(self.scroll)
        self.add_widget(chat_area)

        # --- Divider ---
        class Divider(MDBoxLayout):
            def __init__(self, **kwargs):
                super().__init__(size_hint=(1, None), height=2, **kwargs)
                with self.canvas:
                    Color(0.8, 0.8, 0.8, 1)
                    from kivy.graphics import Rectangle
                    self.rect = Rectangle(pos=self.pos, size=(self.width, 2))
                self.bind(pos=self._update_rect, size=self._update_rect)  # type: ignore
            def _update_rect(self, *args):
                self.rect.pos = self.pos
                self.rect.size = (self.width, 2)
        self.add_widget(Divider())

        # --- Input options for input type dropdown ---
        self.input_options = [
            ("Text", self.set_input_text),
            ("Image", self.set_input_image),
            ("Voice", self.set_input_voice)
        ]
    def set_input_voice(self):
        self.input_menu.dismiss()
        # Do not disable or remove the input field, just update its text
        import threading
        def run_stt():
            try:
                from farmer_agent.nlp.stt import recognize_speech
                result = recognize_speech(source="mic", lang="auto", whisper_model="base")
                def set_text(dt):
                    if result and not str(result).startswith('[Error') and result.strip() and result.strip() != '[Mic Recording Started]':
                        self.text_input.text = result
                    else:
                        self.add_bubble("No speech detected or error.", is_user=False)
                from kivy.clock import Clock
                Clock.schedule_once(set_text, 0)
            except Exception as e:
                def set_error(dt):
                    self.add_bubble(f"Voice input error: {str(e)}", is_user=False)
                from kivy.clock import Clock
                Clock.schedule_once(set_error, 0)
        threading.Thread(target=run_stt, daemon=True).start()

        # --- Input bar (dropdown, text input, send button) ---
        input_bar = MDBoxLayout(size_hint=(1, 0.12), padding=[ChatScreen.get_scaled(16), ChatScreen.get_scaled(8), ChatScreen.get_scaled(16), ChatScreen.get_scaled(8)], spacing=ChatScreen.get_scaled(16))
        self.input_btn = MDRaisedButton(text="📝 Input Type", size_hint=(None, 1), width=140, md_bg_color=(0.13, 0.16, 0.22, 1), text_color=(0.8, 0.9, 1, 1), font_size=ChatScreen.get_scaled(18))
        self.input_menu = MDDropdownMenu(
            caller=None,
            items=[{"text": opt[0], "on_release": opt[1]} for opt in self.input_options]
        )
        self.input_menu.caller = self.input_btn
        self.input_btn.bind(on_release=lambda x: self.input_menu.open())
        input_bar.add_widget(self.input_btn)

        class ModernInput(MDTextField):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.helper_text_mode = "on_focus"
                self.line_color_focus = (33/255, 194/255, 94/255, 1)
                self.line_color_normal = (0.18, 0.22, 0.28, 1)
                self.fill_color = (0.13, 0.16, 0.22, 1)
                self.hint_text = 'Type your message...'
                self.font_size = ChatScreen.get_scaled(18)
                self.padding = [ChatScreen.get_scaled(16), ChatScreen.get_scaled(12), ChatScreen.get_scaled(16), ChatScreen.get_scaled(12)]
                self.radius = [16]
                self.foreground_color = (1, 1, 1, 1)
                self.cursor_color = (1, 1, 1, 1)
                self.hint_text_color = (0.8, 0.95, 0.8, 1)
        self.text_input = ModernInput(size_hint=(0.8, 1), multiline=False)

        from kivy.uix.behaviors import ButtonBehavior
        class ModernButton(MDRaisedButton, ButtonBehavior):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.md_bg_color = (33/255, 194/255, 94/255, 1)
                self.text_color = (1, 1, 1, 1)
                self.font_size = ChatScreen.get_scaled(18)
                self.bold = True
                self.radius = [16]
                with self.canvas.before:
                    Color(0.13, 0.76, 0.37, 0.18)
                    self.shadow_rect = RoundedRectangle(pos=(self.x+2, self.y-2), size=(self.width, self.height), radius=[16])
                self.bind(pos=self._update_bg, size=self._update_bg)
            def _update_bg(self, *args):
                self.shadow_rect.pos = (self.x+2, self.y-2)
                self.shadow_rect.size = self.size
            def on_touch_down(self, touch):
                return bool(super().on_touch_down(touch))
            def on_touch_move(self, touch, *args):  # Unused argument fix
                return super().on_touch_move(touch, *args)
        send_btn = ModernButton(text='➤ Send', size_hint=(0.2, 1))  # Changed send icon
        send_btn.bind(on_release=self.send_message)
        self.mic_btn = None  # Placeholder for mic button
        self.is_recording = False  # Track mic recording state
        input_bar.add_widget(self.text_input)
        input_bar.add_widget(send_btn)
        self.add_widget(input_bar)

        # --- Footer ---
        footer = MDBoxLayout(size_hint=(1, 0.05), padding=[0, ChatScreen.get_scaled(4), 0, ChatScreen.get_scaled(4)])
        footer_label = MDLabel(text='© 2025 Farmer AI Agent | Powered by Open Source | Accessible Design', font_size=ChatScreen.get_scaled(14), color=(0.8, 0.9, 1, 1))
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

    # Removed duplicate _update_bg and mode_bar references

    def _update_bg(self, *args):  # This is not a duplicate - belongs to ChatScreen
        if hasattr(self, 'bg_rect'):
            self.bg_rect.pos = self.pos
            self.bg_rect.size = self.size

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
        self.mode_menu.dismiss()
        func(None)

    def set_input_text(self):
        self.input_menu.dismiss()
        self.text_input.disabled = False
        self.text_input.text = ''
        self.state['input_type'] = 'text'

    def set_input_image(self):
        self.input_menu.dismiss()
        self.text_input.disabled = True
        # Open file chooser popup for image selection with animation
        from kivy.animation import Animation
        filechooser = FileChooserIconView(filters=['*.png', '*.jpg', '*.jpeg', '*.bmp'], path='~')
        popup = Popup(title='Select Image', content=filechooser, size_hint=(0.9, 0.9), opacity=0)
        def animate_open(*args):
            Animation(opacity=1, d=0.35, t='out_quad').start(popup)
        # popup.bind(on_open=animate_open)  # Removed: Popup does not have 'on_open' event
        def on_selection(instance, selection):
            if selection:
                self.state['selected_image'] = selection[0]
                Animation(opacity=0, d=0.25, t='out_quad').start(popup)
                def close_popup(*_):
                    popup.dismiss()
                    self.handle_image_input(selection[0])
                Animation(opacity=0, d=0.25, t='out_quad').bind(on_complete=close_popup)
        filechooser.bind(selection=on_selection) # type: ignore
        popup.open()

    def handle_image_input(self, image_path):
        # This function should handle image input for the current mode
        self.add_bubble(f"Image selected: {image_path}", is_user=True)
        # You can add logic to process the image as per the selected mode

    def set_language(self, lang_code):
        self.language_dropdown.dismiss()
        self.state['language'] = lang_code
        # Translate all UI elements and responses to the selected language
        self.translate_ui(lang_code)
        self.add_bubble(f"Language set to: {lang_code}", is_user=False)

    def translate_ui(self, lang_code):
        # Implement UI translation here
        # Translate static UI text
        translations = {
            'en': {
                'Farmer AI Agent': 'Farmer AI Agent',
                'Select Mode': 'Select Mode',
                'Input Type': 'Input Type',
                'Send': 'Send',
                '🌐 Language': '🌐 Language',
                '© 2025 Farmer AI Agent | Powered by Open Source | Accessible Design': '© 2025 Farmer AI Agent | Powered by Open Source | Accessible Design',
            },
             'ta': {  # Tamil example, you can add more languages
                'Farmer AI Agent': '\u0baa\u0bbe\u0bb0\u0bcd\u0bae\u0bc6\u0bb0\u0bcd \u0a8e\u0b90 \u0b8f\u0b9c\u0bc6\u0ba3\u0bcd\u0b9f\u0bcd',
                'Select Mode': '\u0bae\u0bc1\u0b9f\u0bbf\u0baf\u0bc8 \u0ba4\u0bc6\u0bb0\u0bbf\u0b99\u0bcd\u0b95',
                'Input Type': '\u0b87\u0ba9\u0bcd\u0baa\u0bc1\u0b9f\u0bcd \u0b95\u0bcd\u0bb3\u0bbf',
                'Send': '\u0b85\u0ba9\u0bc1\u0baa\u0bc1',
                '🌐 Language': '\u0bae\u0bca\u0bb4\u0bbf',
                '© 2025 Farmer AI Agent | Powered by Open Source | Accessible Design': '© 2025 \u0baa\u0bbe\u0bb0\u0bcd\u0bae\u0bc6\u0bb0\u0bcd \u0b8e\u0b90 \u0b8f\u0b9c\u0bc6\u0ba3\u0bcd\u0b9f\u0bcd | \u0b92\u0baa\u0ba9\u0bcd \u0b9a\u0bcb\u0bb0\u0bcd\u0baa\u0bcd | \u0b85\u0ba3\u0bcd\u0baa\u0bc1\u0b95\u0bae\u0bcd \u0ba8\u0bc6\u0bb1\u0bbf\u0b95\u0bcd\u0b95\u0bc1\u0bae\u0bcd',
            },
             # Add more language translations as needed, for example Hindi
             # 'hi': { ... }
        }
        lang_map = translations.get(lang_code, translations['en'])
        # Update header
        self.children[-1].children[1].text = lang_map['Farmer AI Agent']
        # Update mode dropdown button
        self.mode_btn.text = lang_map['Select Mode']
        # Update input dropdown button
        self.input_btn.text = lang_map['Input Type']
        # Update send button
        self.children[-3].children[0].text = lang_map['Send']
        # Update language button
        self.language_btn.text = lang_map['🌐 Language']
        # Update footer
        self.children[0].children[0].text = lang_map['© 2025 Farmer AI Agent | Powered by Open Source | Accessible Design']
        # Optionally, translate chat bubbles and other dynamic content

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
            # Show calendar options as clickable buttons
            options = [
                ("View crop schedule", "1"),
                ("List crops", "2"),
                ("Add reminder", "3"),
                ("Add recurring reminder", "4"),
                ("Delete reminder", "5"),
                ("Next activity", "6")
            ]
            option_layout = MDBoxLayout(orientation='vertical', size_hint_y=None)
            option_layout.bind(minimum_height=option_layout.setter('height'))
            for label, value in options:
                btn = MDRectangleFlatButton(text=f"{label}", size_hint_y=None, height=52, md_bg_color=(33/255, 194/255, 94/255, 1), text_color=(1,1,1,1), font_size=18)
                btn.bind(on_release=lambda btn, v=value: self.calendar_option_selected(v))
                option_layout.add_widget(btn)
            from kivy.animation import Animation
            popup = MDDialog(
                title="Calendar Options",
                type="custom",
                content_cls=option_layout,
                size_hint=(0.7, None),
                height=52 * len(options) + 80,
                opacity=0
            )
            self._calendar_popup = popup
            def animate_open(*args):
                Animation(opacity=1, d=0.35, t='out_quad').start(popup)
            popup.bind(on_open=animate_open)
            popup.open()
        except Exception as e:
            logging.error(f"calendar_action error: {str(e)}")
            self.add_bubble(f"Calendar module error: {str(e)}", is_user=False)

    def calendar_option_selected(self, value):
        # Close the popup and pass the value as if user typed it
        if hasattr(self, '_calendar_popup') and self._calendar_popup:
            self._calendar_popup.dismiss()
            self._calendar_popup = None
        self.send_message(type('FakeInstance', (), {'text': value})())

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
                estimator = WeatherEstimator() # type: ignore
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
                analytics = Analytics() # type: ignore
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
                    list_voices() # type: ignore
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
                        advice = get_crop_advice(crop) # type: ignore
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
                        faq = FAQ() # type: ignore
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
                        translator = OfflineTranslator() # type: ignore
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
                            self.mic_btn = MDRectangleFlatButton(text="🎤 Mic", size_hint=(None, None), size=(120, 44), md_bg_color=(0.2, 0.6, 0.2, 1), text_color=(1, 1, 1, 1))  # Increased mic button width
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
                        logging.exception("Text-to-speech error")
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
                if self.mic_btn:
                    self.mic_btn.text = "⏹ Stop Mic"
                self.add_bubble("Recording... Please speak into the mic. Click again to stop.", is_user=False)
            else:
                self.is_recording = False
                if self.mic_btn:
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
                self.calendar = CropCalendar() # type: ignore
                self.reminders = Reminders() # type: ignore
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

class FarmerAgentApp(MDApp):
    def build(self):
        return ChatScreen()

if __name__ == "__main__":
    FarmerAgentApp().run()