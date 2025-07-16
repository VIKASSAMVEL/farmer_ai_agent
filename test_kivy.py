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
from kivy.core.window import Window
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup
from kivy.animation import Animation
from kivy.uix.behaviors import ButtonBehavior
from farmer_agent.utils.language_utils import detect_language, llm_translate

# Configure logging
logging.basicConfig(
    filename='kivy_chat_log.txt',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s',
    encoding='utf-8'
)

# Helper function to get font path with fallback
def get_font_path(font_name):
    base_path = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(base_path, 'fonts', f'{font_name}.ttf')
    if os.path.exists(font_path):
        return font_path
    logging.warning(f"Font file {font_path} not found, falling back to default font.")
    return 'Roboto'  # Fallback to KivyMD's default font

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

# Define custom widgets outside ChatScreen to avoid redefinition
class Divider(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(size_hint=(1, None), height=2, **kwargs)
        with self.canvas:
            Color(0.8, 0.8, 0.8, 1)
            self.rect = Rectangle(pos=self.pos, size=(self.width, 2))
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = (self.width, 2)

class ModernInput(MDTextField):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.helper_text_mode = "on_focus"
        self.line_color_focus = (33/255, 194/255, 94/255, 1)
        self.line_color_normal = (0.18, 0.22, 0.28, 1)
        self.fill_color = (0.13, 0.16, 0.22, 1)
        self.hint_text = 'Type your message...'
        self.font_size = 24  # Increased from 18
        self.padding = [20, 16, 20, 16]  # Adjusted for larger text
        self.radius = [16]
        self.foreground_color = (1, 1, 1, 1)
        self.cursor_color = (1, 1, 1, 1)
        self.hint_text_color = (0.8, 0.95, 0.8, 1)
        self.helper_text_font_size = 18  # Increased for hint text

class ModernButton(MDRaisedButton, ButtonBehavior):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = (33/255, 194/255, 94/255, 1)
        self.text_color = (1, 1, 1, 1)
        self.font_size = 24  # Increased from 18
        self.bold = True
        self.radius = [16]
        with self.canvas.before:
            Color(0.13, 0.76, 0.37, 0.18)
            self.shadow_rect = RoundedRectangle(pos=(self.x+2, self.y-2), size=(self.width, self.height), radius=[16])
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *args):
        self.shadow_rect.pos = (self.x+2, self.y-2)
        self.shadow_rect.size = (self.width, self.height)

    def on_touch_down(self, touch):
        result = super().on_touch_down(touch)
        return bool(result)

    def on_touch_move(self, touch, *args):
        return super().on_touch_move(touch, *args)

class ChatBubble(MDBoxLayout):
    def __init__(self, text, is_user=False, **kwargs):
        super().__init__(orientation='horizontal', size_hint_y=None, padding=[20, 20, 20, 20], **kwargs)  # Increased padding
        timestamp = datetime.now().strftime('%H:%M')
        bubble_color = (33/255, 194/255, 94/255, 1) if is_user else (27/255, 38/255, 59/255, 1)
        avatar_size = 48  # Slightly increased to match larger text
        avatar_text = '🧑' if is_user else '🌾'
        # Use local Segoe UI Emoji.ttf for emoji rendering
        def get_emoji_font_path():
            base_path = os.path.dirname(os.path.abspath(__file__))
            font_path = os.path.join(base_path, 'fonts', 'Segoe UI Emoji.ttf')
            if os.path.exists(font_path):
                return font_path
            return 'Segoe UI Emoji'  # Fallback to system font

        avatar = MDLabel(
            text=avatar_text,
            font_style='H5',
            font_name=get_emoji_font_path(),
            size_hint=(None, None),
            size=(avatar_size, avatar_size),
            theme_text_color='Custom',
            text_color=(0.2, 0.4, 1, 1)
        )
        self.label = MDLabel(
            text=text,
            font_name=get_font_path('NotoSans-Regular'),
            size_hint_x=0.75,
            halign='right' if is_user else 'left',
            valign='middle',
            theme_text_color='Custom',
            text_color=(1, 1, 1, 1) if is_user else (0.9, 0.9, 0.9, 1),
            font_style='Body2',
            font_size=48,  # Increased from 36
            opacity=0,
            line_height=2.2  # Increased from 2.0
        )
        self.label.bind(texture_size=self._update_height)
        self.timestamp_label = MDLabel(
            text=timestamp,
            font_name=get_font_path('NotoSans-Regular'),
            size_hint_x=0.15,
            font_style='Caption',
            theme_text_color='Custom',
            text_color=(0.2, 0.4, 1, 1),
            halign='left' if is_user else 'right',
            valign='bottom',
            font_size=28  # Increased from 22
        )
        if is_user:
            self.add_widget(self.timestamp_label)
            self.add_widget(self.label)
            self.add_widget(avatar)
        else:
            self.add_widget(avatar)
            self.add_widget(self.label)
            self.add_widget(self.timestamp_label)
        Animation(opacity=1, d=0.4, t='out_quad').start(self.label)

    def _update_height(self, *args):
        min_height = 64  # Increased to accommodate larger text
        padding = 32  # Increased padding
        self.label.height = max(self.label.texture_size[1] + padding, min_height)
        self.height = self.label.height + 16

def show_debug_popup(error_msg):
    content = MDBoxLayout(orientation='vertical')
    label = MDLabel(
        text=error_msg,
        size_hint_y=None,
        height=400,
        font_name=get_font_path('NotoSans-Regular'),
        font_size=24  # Increased for readability
    )
    btn = MDRectangleFlatButton(
        text='Close',
        size_hint_y=None,
        height=48,
        font_size=24  # Increased
    )
    content.add_widget(label)
    content.add_widget(btn)
    popup = MDDialog(
        title='Debugger - Error Traceback',
        content=content,
        size_hint=(0.9, 0.7)
    )
    btn.bind(on_release=popup.dismiss)
    popup.open()

class ChatScreen(MDBoxLayout):

    def add_bubble(self, text, is_user=False):
        import re
        import threading
        import time
        lang = self.state.get('language', 'en')
        orig_text = text
        spinner_bubble = None

        def format_structured(obj, indent=0):
            spacer = '  ' * indent
            if isinstance(obj, dict):
                lines = []
                for k, v in obj.items():
                    if isinstance(v, (dict, list)):
                        lines.append(f"{spacer}{k}:")
                        lines.append(format_structured(v, indent + 1))
                    else:
                        lines.append(f"{spacer}{k}: {v}")
                return '\n'.join(lines)
            elif isinstance(obj, list):
                return '\n'.join([f"{spacer}• {format_structured(item, indent + 1) if isinstance(item, (dict, list)) else item}" for item in obj])
            else:
                return str(obj)

        def remove_escape_sequences(s):
            if not isinstance(s, str):
                return s
            s = s.replace('\\n', '\n').replace('\\t', '    ').replace('\\r', '')
            s = re.sub(r'\\(?!n|t|r)', '', s)
            return s

        def show_spinner(dt=None):
            nonlocal spinner_bubble
            spinner_bubble = ChatBubble("Processing...", is_user=False)
            self.chat_history.add_widget(spinner_bubble)
            self.chat_history.height = self.chat_history.minimum_height
            self.scroll.scroll_to(spinner_bubble, padding=10, animate=True)

        def remove_spinner():
            if spinner_bubble and spinner_bubble.parent:
                self.chat_history.remove_widget(spinner_bubble)
                self.chat_history.height = self.chat_history.minimum_height

        try:
            # Only show spinner and translate if not user and not English
            translated_text = orig_text
            if not is_user and lang != 'en':
                from kivy.clock import Clock
                Clock.schedule_once(show_spinner, 0)
                def do_translation():
                    import queue
                    translated = orig_text
                    try:
                        # Timeout for translation (5 seconds)
                        result_queue = queue.Queue()
                        def target():
                            try:
                                result_queue.put(self.llm_translate(orig_text, lang, source_lang='en'))
                            except Exception:
                                result_queue.put(None)
                        t = threading.Thread(target=target)
                        t.start()
                        t.join(timeout=5)
                        if t.is_alive():
                            translated = orig_text  # fallback to English
                        else:
                            try:
                                result = result_queue.get_nowait()
                                if result is None:
                                    translated = orig_text
                                else:
                                    translated = result
                            except Exception:
                                translated = orig_text
                    except Exception:
                        translated = orig_text
                    return translated
                translated_text = do_translation()
                remove_spinner()
            formatted_text = translated_text
            if not is_user:
                try:
                    if isinstance(orig_text, str):
                        stripped = orig_text.strip()
                        if (stripped.startswith('{') and stripped.endswith('}')) or (stripped.startswith('[') and stripped.endswith(']')):
                            obj = json.loads(stripped)
                            formatted_text = format_structured(obj)
                except Exception:
                    pass
            formatted_text = remove_escape_sequences(formatted_text)
            bubble = ChatBubble(formatted_text, is_user=is_user)
            self.chat_history.add_widget(bubble)
            self.chat_history.height = self.chat_history.minimum_height
            self.scroll.scroll_to(bubble, padding=10, animate=True)
            prefix = 'USER' if is_user else 'AGENT'
            logging.info(f"[{prefix}] {orig_text}")
            if orig_text == 'User history cleared.':
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
            remove_spinner()
            logging.error(f"add_bubble error: {str(e)}")
            self.add_bubble(f"Error displaying message: {str(e)}", is_user=False)


    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.state = {'mode': 'chat', 'input_type': 'text', 'language': 'en', 'context': {}}
        self.calendar = CropCalendar() if CropCalendar else None
        self.reminders = Reminders() if Reminders else None
        self.voice_output_enabled = False
        self.detect_language = detect_language
        self.llm_translate = llm_translate
        self.bind(pos=self._update_bg, size=self._update_bg)

        # Mode bar
        self.mode_bar = MDBoxLayout(size_hint=(1, 0.09), padding=[16, 8, 16, 8], spacing=16)
        self.mode_btn = MDRaisedButton(
            text="Select Mode",
            size_hint=(None, 1),
            width=140,
            md_bg_color=(0.13, 0.16, 0.22, 1),
            text_color=(0.8, 0.9, 1, 1),
            font_size=24
        )
        self.mode_menu = MDDropdownMenu(
            caller=self.mode_btn,
            items=[
                {"text": "Advisory", "on_release": lambda: self.advisory_action(None)},
                {"text": "Calendar", "on_release": lambda: self.calendar_action(None)},
                {"text": "FAQ", "on_release": lambda: self.faq_action(None)},
                {"text": "Weather", "on_release": lambda: self.weather_action(None)},
                {"text": "Analytics", "on_release": lambda: self.analytics_action(None)},
                {"text": "Chat", "on_release": lambda: self.chat_action(None)},
                {"text": "Clear History", "on_release": lambda: self.clear_history_action(None)},
                {"text": "Exit", "on_release": lambda: self.exit_action(None)},
            ]
        )
        self.mode_btn.bind(on_release=lambda _: self.mode_menu.open())
        self.mode_bar.add_widget(self.mode_btn)
        self.language_btn = MDRaisedButton(
            text="Language",
            size_hint=(None, 1),
            width=140,
            md_bg_color=(0.13, 0.16, 0.22, 1),
            text_color=(0.8, 0.9, 1, 1),
            font_size=24,
            font_name=get_font_path('NotoSans-Regular')
        )
        self._lang_btn_default_bg = (0.13, 0.16, 0.22, 1)
        self._lang_btn_active_bg = (0.22, 0.28, 0.36, 1)
        self._lang_btn_default_text = (0.8, 0.9, 1, 1)
        self._lang_btn_active_text = (1, 1, 1, 1)
        self.supported_languages = [
            ("English", "en"),
            ("தமிழ்", "ta"),
            ("हिन्दी", "hi"),
        ]
        font_paths = {
            "en": get_font_path('NotoSans-Regular'),
            "ta": get_font_path('NotoSansTamil-Regular'),
            "hi": get_font_path('NotoSansDevanagari-Regular'),
        }
        self.language_dropdown = MDDropdownMenu(
            caller=self.language_btn,
            items=[{
                "text": name,
                "on_release": (lambda code=code: self.set_language(code)),
                "viewclass": "MDRaisedButton",
                "font_name": font_paths.get(code, font_paths["en"]),
                "md_bg_color": (0.13, 0.16, 0.22, 1),
                "text_color": (0.8, 0.9, 1, 1),
                "font_size": 22,
                "size_hint_y": None,
                "height": 48,
                "radius": [12],
                "halign": "center"
            } for name, code in self.supported_languages]
        )
        def on_lang_menu_open(*_):
            self.language_btn.md_bg_color = self._lang_btn_active_bg
            self.language_btn.text_color = self._lang_btn_active_text
        def on_lang_menu_dismiss(*_):
            self.language_btn.md_bg_color = self._lang_btn_default_bg
            self.language_btn.text_color = self._lang_btn_default_text
        self.language_dropdown.bind(on_open=on_lang_menu_open, on_dismiss=on_lang_menu_dismiss)
        self.language_btn.bind(on_release=lambda _: self.language_dropdown.open())
        self.mode_bar.add_widget(self.language_btn)
        self.add_widget(self.mode_bar)

        # Chat history area
        chat_area = MDBoxLayout(size_hint=(1, 0.62), padding=[16, 8, 16, 8])
        self.chat_history = MDGridLayout(cols=1, spacing=14, size_hint_y=None)
        self.chat_history.bind(minimum_height=self.chat_history.setter('height'))
        self.scroll = MDScrollView(size_hint=(1, 1))
        self.scroll.add_widget(self.chat_history)
        chat_area.add_widget(self.scroll)
        self.add_widget(chat_area)

        # Now it's safe to show the initial chat bubble
        self.add_bubble("Chat mode enabled. You can now chat directly with the AI. Type your message:", is_user=False)

        # Divider
        self.add_widget(Divider())

        # Input options
        self.input_options = [
            ("Text", self.set_input_text),
            ("Image", self.set_input_image),
            ("Voice", self.set_input_voice)
        ]

        # Input bar
        self.input_bar = MDBoxLayout(size_hint=(1, 0.12), padding=[16, 8, 16, 8], spacing=16)
        self.input_btn = MDRaisedButton(
            text="📝 Input Type",
            size_hint=(None, 1),
            width=140,
            md_bg_color=(0.13, 0.16, 0.22, 1),
            text_color=(0.8, 0.9, 1, 1),
            font_size=24
        )
        self.input_menu = MDDropdownMenu(
            caller=self.input_btn,
            items=[{"text": opt[0], "on_release": opt[1]} for opt in self.input_options]
        )
        self.input_btn.bind(on_release=lambda _: self.input_menu.open())
        self.input_bar.add_widget(self.input_btn)
        self.text_input = ModernInput(size_hint=(0.8, 1), multiline=False)
        send_btn = ModernButton(text='Send', size_hint=(0.2, 1))
        send_btn.bind(on_release=self.send_message)
        self.mic_btn = None
        self.is_recording = False
        self.input_bar.add_widget(self.text_input)
        self.input_bar.add_widget(send_btn)
        self.add_widget(self.input_bar)

        # Footer
        footer = MDBoxLayout(size_hint=(1, 0.05), padding=[0, 4, 0, 4])
        footer_label = MDLabel(
            text='© 2025 Farmer AI Agent | Powered by Open Source | Accessible Design',
            font_size=20,
            color=(0.8, 0.9, 1, 1),
            font_name=get_font_path('NotoSans-Regular')
        )
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
    def chat_action(self, instance):
        self.state["mode"] = "chat"
        self.add_bubble("Chat mode enabled. You can now chat directly with the AI. Type your message:", is_user=False)

    def _update_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0, 0, 0, 1)  # Black background
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

    def set_input_text(self):
        self.input_menu.dismiss()
        self.text_input.disabled = False
        self.text_input.text = ''
        self.state['input_type'] = 'text'

    def set_input_image(self):
        self.input_menu.dismiss()
        self.text_input.disabled = True
        filechooser = FileChooserIconView(filters=['*.png', '*.jpg', '*.jpeg', '*.bmp'], path='~')
        popup = Popup(title='Select Image', content=filechooser, size_hint=(0.9, 0.9), opacity=0)
        Animation(opacity=1, d=0.35, t='out_quad').start(popup)

        def on_selection(instance, selection):
            if selection:
                self.state['selected_image'] = selection[0]
                anim = Animation(opacity=0, d=0.25, t='out_quad')
                anim.bind(on_complete=lambda *args: popup.dismiss())
                anim.start(popup)
                self.handle_image_input(selection[0])

        if hasattr(filechooser, 'bind'):
            filechooser.bind(selection=on_selection) # type: ignore
        popup.open()

    def handle_image_input(self, image_path):
        self.add_bubble(f"Image selected: {image_path}", is_user=True)
        if PlantIdentifier:
            spinner = MDSpinner(size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.5, 'center_y': 0.5})
            self.chat_history.add_widget(spinner)
            self.text_input.disabled = True
            def run_image():
                result_bubbles = []
                try:
                    identifier = PlantIdentifier() # type: ignore
                    plant_result = identifier.identify(image_path)
                    result_bubbles.append((f"Plant Identification Result: {plant_result}", False))
                    tips = identifier.get_llm_disease_tips(plant_result)
                    result_bubbles.append(("LLM Tips for Disease Solution/Medicine:", False))
                    result_bubbles.append((tips, False))
                except Exception as e:
                    logging.error(f"image_identification error: {str(e)}")
                    result_bubbles.append((f"Error in plant identification: {str(e)}", False))
                finally:
                    Clock.schedule_once(lambda dt: self._update_ui(spinner, result_bubbles), 0)
            threading.Thread(target=run_image, daemon=True).start()
        else:
            self.add_bubble("Plant identification module not available.", is_user=False)

    def set_input_voice(self):
        self.input_menu.dismiss()
        self.text_input.disabled = True
        if not self.mic_btn:
            self.mic_btn = MDRectangleFlatButton(
                text="🎤 Mic",
                size_hint=(None, None),
                size=(120, 48),
                md_bg_color=(0.2, 0.6, 0.2, 1),
                text_color=(1, 1, 1, 1),
                font_size=24  # Increased
            )
            self.mic_btn.bind(on_release=self.start_mic_recording)
            self.input_bar.add_widget(self.mic_btn)
        self.add_bubble("Click the Mic button to start/stop recording.", is_user=False)

    def set_language(self, lang_code):
        self.language_dropdown.dismiss()
        self.state['language'] = lang_code
        self.translate_ui(lang_code)
        self.add_bubble(f"Language set to: {lang_code}", is_user=False)

    def auto_detect_and_set_language(self, text):
        detected = self.detect_language(text)
        if detected != self.state['language']:
            self.set_language(detected)

    def translate_ui(self, lang_code):
        # Centralized translation dictionary for UI strings
        translations = {
            'en': {
                'Farmer AI Agent': 'Farmer AI Agent',
                'Select Mode': 'Select Mode',
                'Input Type': 'Input Type',
                'Send': 'Send',
                'Language': 'Language',
                '© 2025 Farmer AI Agent | Powered by Open Source | Accessible Design': '© 2025 Farmer AI Agent | Powered by Open Source | Accessible Design',
            },
            'ta': {
                'Farmer AI Agent': 'பார்மர் எஐ ஏஜெண்ட்',
                'Select Mode': 'முறையை தேர்ந்தெடு',
                'Input Type': 'இன்புட் வகை',
                'Send': 'அனுப்பு',
                'Language': 'மொழி',
                '© 2025 Farmer AI Agent | Powered by Open Source | Accessible Design': '© 2025 பார்மர் எஐ ஏஜெண்ட் | ஓப்பன் சோர்ஸ் மூலம் இயக்கப்படுகிறது | அணுகக்கூடிய வடிவமைப்பு',
            },
            'hi': {
                'Farmer AI Agent': 'किसान एआई एजेंट',
                'Select Mode': 'मोड चुनें',
                'Input Type': 'इनपुट प्रकार',
                'Send': 'भेजें',
                'Language': 'भाषा',
                '© 2025 Farmer AI Agent | Powered by Open Source | Accessible Design': '© 2025 किसान एआई एजेंट | ओपन सोर्स द्वारा संचालित | सुलभ डिज़ाइन',
            },
            'te': {
                'Farmer AI Agent': 'రైతు ఏఐ ఏజెంట్',
                'Select Mode': 'మోడ్ ఎంచుకోండి',
                'Input Type': 'ఇన్పుట్ రకం',
                'Send': 'పంపు',
                'Language': 'భాష',
                '© 2025 Farmer AI Agent | Powered by Open Source | Accessible Design': '© 2025 రైతు ఏఐ ఏజెంట్ | ఓపెన్ సోర్స్ ఆధారితం | అందుబాటులో ఉన్న డిజైన్',
            },
            'kn': {
                'Farmer AI Agent': 'ರೈತ ಎಐ ಏಜೆಂಟ್',
                'Select Mode': 'ಮೋಡ್ ಆಯ್ಕೆಮಾಡಿ',
                'Input Type': 'ಇನ್ಪುಟ್ ಪ್ರಕಾರ',
                'Send': 'ಕಳುಹಿಸಿ',
                'Language': 'ಭಾಷೆ',
                '© 2025 Farmer AI Agent | Powered by Open Source | Accessible Design': '© 2025 ರೈತ ಎಐ ಏಜೆಂಟ್ | ಓಪನ್ ಸೋರ್ಸ್ ಮೂಲಕ ಚಾಲಿತ | ಸುಲಭವಾದ ವಿನ್ಯಾಸ',
            },
            'ml': {
                'Farmer AI Agent': 'കർഷകൻ എഐ ഏജന്റ്',
                'Select Mode': 'മോഡ് തിരഞ്ഞെടുക്കുക',
                'Input Type': 'ഇൻപുട്ട് തരം',
                'Send': 'അയയ്ക്കുക',
                'Language': 'ഭാഷ',
                '© 2025 Farmer AI Agent | Powered by Open Source | Accessible Design': '© 2025 കർഷകൻ എഐ ഏജന്റ് | ഓപ്പൺ സോഴ്സ് ഉപയോഗിച്ച് പ്രവർത്തിക്കുന്നു | ആക്സസിബിൾ ഡിസൈൻ',
            },
            # Add more translations as needed
        }
        font_paths = {
            "en": get_font_path('NotoSans-Regular'),
            "ta": get_font_path('NotoSansTamil-Regular'),
            "hi": get_font_path('NotoSansDevanagari-Regular'),
        }
        font_name = font_paths.get(lang_code, font_paths["en"])
        lang_map = translations.get(lang_code, translations['en'])
        self.mode_btn.text = lang_map.get('Select Mode', 'Select Mode')
        self.mode_btn.font_name = font_name
        self.input_btn.text = lang_map.get('Input Type', 'Input Type')
        self.input_btn.font_name = font_name
        # Send button is the rightmost child in input_bar
        send_btn = self.input_bar.children[0]
        send_btn.text = lang_map.get('Send', 'Send')
        if hasattr(send_btn, 'font_name'):
            send_btn.font_name = font_name
        self.language_btn.text = lang_map.get('Language', 'Language')
        self.language_btn.font_name = font_name
        # Footer label is the only child of the footer box (which is the first child of self.children)
        footer_label = self.children[0].children[0]
        footer_label.text = lang_map.get('© 2025 Farmer AI Agent | Powered by Open Source | Accessible Design', '© 2025 Farmer AI Agent | Powered by Open Source | Accessible Design')
        if hasattr(footer_label, 'font_name'):
            footer_label.font_name = font_name

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
            size=(200, 48),
            pos_hint={'center_x': 0.5},
            font_size=24  # Increased
        )
        def on_crop_select(spinner, text):
            self.text_input.text = text
            self.state["mode"] = "advisory_crop"
            self.chat_history.remove_widget(crop_spinner)
            self.send_message(None)
        if hasattr(crop_spinner, 'bind'):
            crop_spinner.bind(text=on_crop_select) # type: ignore
        self.chat_history.add_widget(crop_spinner)

    def input_action(self, instance):
        self.state["mode"] = "input"
        self.add_bubble("Input Options:\n1. Voice\n2. Audio File\n3. Text\n4. Image", is_user=False)

    def calendar_action(self, instance):
        if not CropCalendar or not Reminders:
            self.add_bubble("Calendar module not available.", is_user=False)
            return
        self.state["mode"] = "calendar_option"
        self.add_bubble(
            "Calendar Options:\n1. Show crop calendar\n2. List crops\n3. Add reminder\n4. Add recurring reminder\n5. Delete reminders\n6. Next activity",
            is_user=False
        )

    def faq_action(self, instance):
        if not FAQ:
            self.add_bubble("FAQ module not available.", is_user=False)
            return
        self.state["mode"] = "faq"
        self.add_bubble("Enter your question:", is_user=False)

    def toggle_voice_output(self):
        self.voice_output_enabled = not self.voice_output_enabled
        status = "enabled" if self.voice_output_enabled else "disabled"
        self.add_bubble(f"Voice output {status}.", is_user=False)

    def weather_action(self, instance):
        if not WeatherEstimator:
            self.add_bubble("Weather module not available.", is_user=False)
            return
        spinner = MDSpinner(size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.chat_history.add_widget(spinner)
        self.text_input.disabled = True
        def run_weather():
            result_bubbles = []
            try:
                estimator = WeatherEstimator() # type: ignore
                location = estimator.get_current_location()
                if location:
                    weather = estimator.fetch_openweather(location)
                    if weather:
                        tips = estimator.get_llm_weather_tips(weather)
                        weather_str = f"[b]Current Weather for {location}:[/b]\n" + json.dumps(weather, indent=2, ensure_ascii=False)
                        combined = f"{weather_str}\n\n[b]Farming Tips:[/b]\n{tips}"
                        result_bubbles.append((combined, False))
                    else:
                        result_bubbles.append(("Could not fetch current weather. Check API key or location.", False))
                else:
                    result_bubbles.append(("Could not detect location.", False))
            except Exception as e:
                result_bubbles.append((f"Weather error: {str(e)}", False))
            finally:
                Clock.schedule_once(lambda dt: self._update_ui(spinner, result_bubbles), 0)
        threading.Thread(target=run_weather, daemon=True).start()

    def translate_action(self, instance):
        if not OfflineTranslator:
            self.add_bubble("Translate module not available.", is_user=False)
            return
        self.state["mode"] = "translate_text"
        self.add_bubble("Enter text to translate from English:", is_user=False)

    def analytics_action(self, instance):
        if not Analytics:
            self.add_bubble("Analytics module not available.", is_user=False)
            return
        spinner = MDSpinner(size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.5, 'center_y': 0.5})
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
        threading.Thread(target=run_analytics, daemon=True).start()

    def tts_voices_action(self, instance):
        if not list_voices:
            self.add_bubble("TTS Voices module not available.", is_user=False)
            return
        spinner = MDSpinner(size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.5, 'center_y': 0.5})
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
        threading.Thread(target=run_tts_voices, daemon=True).start()

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

    def start_mic_recording(self, instance):
        try:
            import threading
            import time
            if not recognize_speech:
                self.add_bubble("Voice input not available.", is_user=False)
                return
            if not hasattr(self, '_mic_stop_event'):
                self._mic_stop_event = threading.Event()
                self._mic_thread = None
            if not self.is_recording:
                self.is_recording = True
                self._mic_stop_event.clear()
                if self.mic_btn:
                    self.mic_btn.text = "⏹ Stop Mic"
                self.add_bubble("Recording... Please speak into the mic. Click again to stop.", is_user=False)
                def run_stt():
                    try:
                        # Start recording, but wait for stop event
                        text_result = [""]  # Initialize as list of str for type compatibility
                        def record():
                            # recognize_speech should block until stopped, but if not, we simulate with event
                            lang_code = self.state.get('language', 'en') or 'en'
                            # Whisper expects ISO codes, not 'auto'
                            if lang_code == 'auto':
                                lang_code = 'en'
                            try:
                                text_result[0] = recognize_speech(source='mic', lang=lang_code) # type: ignore
                            except Exception as e:
                                text_result[0] = f"[Error] {str(e)}"
                        rec_thread = threading.Thread(target=record)
                        rec_thread.start()
                        # Wait for user to click stop
                        self._mic_stop_event.wait()
                        # If recognize_speech is blocking, it should stop on its own; if not, we just use the result
                        rec_thread.join(timeout=2)
                        text = text_result[0]
                        def set_text(dt):
                            if text and not str(text).startswith('[Error') and text.strip() and text.strip() != '[Mic Recording Started]':
                                self.add_bubble(f"Mic Input: {text}", is_user=True)
                                self.text_input.text = text
                                self.send_message(None)
                            else:
                                self.add_bubble("No speech detected. Please try again or check your microphone.", is_user=False)
                            self.is_recording = False
                            if self.mic_btn:
                                self.mic_btn.text = "🎤 Mic"
                        Clock.schedule_once(set_text, 0)
                    except Exception as e:
                        def set_error(dt):
                            self.add_bubble(f"Mic error: {str(e)}", is_user=False)
                            self.is_recording = False
                            if self.mic_btn:
                                self.mic_btn.text = "🎤 Mic"
                        Clock.schedule_once(set_error, 0)
                self._mic_thread = threading.Thread(target=run_stt, daemon=True)
                self._mic_thread.start()
            else:
                # User clicked again to stop
                self.is_recording = False
                if hasattr(self, '_mic_stop_event'):
                    self._mic_stop_event.set()
                if self.mic_btn:
                    self.mic_btn.text = "🎤 Mic"
        except Exception as e:
            self.add_bubble(f"Mic error: {str(e)}", is_user=False)
            self.is_recording = False
            if self.mic_btn:
                self.mic_btn.text = "🎤 Mic"

    def handle_calendar_option(self, user_text):
        option = user_text.strip()
        try:
            if not self.calendar or not self.reminders:
                self.add_bubble("Calendar module not available.", is_user=False)
                self.state["mode"] = None
                return
            if option == "1":
                self.add_bubble("Enter crop name:", is_user=False)
                self.state["mode"] = "calendar_crop"
            elif option == "2":
                crops = self.calendar.list_crops()
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

    def send_message(self, instance):
        user_text = self.text_input.text.strip()
        if not user_text:
            return
        # Auto-detect user language and set UI
        self.auto_detect_and_set_language(user_text)
        self.add_bubble(user_text, is_user=True)
        try:
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
            if self.state.get("mode") == "calendar_option":
                self.handle_calendar_option(user_text)
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
            elif self.state.get("mode") == "recurring_interval":
                try:
                    self.state["context"]["recurring_interval"] = int(user_text.strip())
                    self.add_bubble("Occurrences:", is_user=False)
                    self.state["mode"] = "recurring_occurrences"
                except ValueError:
                    self.add_bubble("Error: Invalid interval.", is_user=False)
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
                spinner = MDSpinner(size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.5, 'center_y': 0.5})
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
                        # Show LLM advice as a separate bubble for clarity
                        if 'llm_advice' in advice and advice['llm_advice']:
                            result_bubbles.append(("LLM Expert Advice:", False))
                            result_bubbles.append((advice['llm_advice'], False))
                        self.state["context"]["last_advisory"] = advice
                        self.state["context"]["last_advisory_crop"] = crop
                        self.state["mode"] = "advisory_feedback"
                        result_bubbles.append(("Was this advice helpful? (y/n):", False))
                    except Exception as e:
                        logging.error(f"advisory_action error: {str(e)}")
                        result_bubbles.append((f"Error: {str(e)}", False))
                    finally:
                        Clock.schedule_once(lambda dt: self._update_ui(spinner, result_bubbles), 0)
                threading.Thread(target=run_advisory, daemon=True).start()
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
                spinner = MDSpinner(size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.5, 'center_y': 0.5})
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
                            if speak and self.voice_output_enabled:
                                speak(answer)
                        else:
                            result_bubbles.append(("No response from LLM.", False))
                    except Exception as e:
                        logging.error(f"faq_action error: {str(e)}")
                        result_bubbles.append((f"FAQ error: {str(e)}", False))
                    finally:
                        Clock.schedule_once(lambda dt: self._update_ui(spinner, result_bubbles), 0)
                threading.Thread(target=run_faq, daemon=True).start()
            elif self.state.get("mode") == "translate_text":
                self.state["context"]["translate_text"] = user_text.strip()
                self.add_bubble("Enter target language code (hi=Hindi, ta=Tamil, te=Telugu, kn=Kannada, ml=Malayalam):", is_user=False)
                self.state["mode"] = "translate_lang"
            elif self.state.get("mode") == "translate_lang":
                tgt_lang = user_text.strip() or "hi"
                spinner = MDSpinner(size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.5, 'center_y': 0.5})
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
                threading.Thread(target=run_translate, daemon=True).start()
                self.state["mode"] = None
            elif self.state.get("mode") == "input":
                mode = user_text.strip()
                if mode == "1":
                    self.set_input_voice()
                elif mode == "2":
                    self.add_bubble("Enter audio file path:", is_user=False)
                    self.state["mode"] = "audio_file"
                elif mode == "3":
                    self.add_bubble("Enter your request:", is_user=False)
                    self.state["mode"] = "text_input"
                elif mode == "4":
                    self.set_input_image()
                else:
                    self.add_bubble("Invalid input mode.", is_user=False)
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
                spinner = MDSpinner(size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.5, 'center_y': 0.5})
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
                threading.Thread(target=run_audio, daemon=True).start()
                self.state["mode"] = None
            elif self.state.get("mode") == "chat":
                spinner = MDSpinner(size_hint=(None, None), size=(50, 50), pos_hint={'center_x': 0.5, 'center_y': 0.5})
                self.chat_history.add_widget(spinner)
                self.text_input.disabled = True
                def run_llm_chat():
                    result_bubbles = []
                    try:
                        # Use LLM utility to get a response
                        from farmer_agent.utils.llm_utils import call_llm
                        response = call_llm(user_text)
                        result_bubbles.append((response, False))
                    except Exception as e:
                        result_bubbles.append((f"Chat error: {str(e)}", False))
                    finally:
                        Clock.schedule_once(lambda dt: self._update_ui(spinner, result_bubbles), 0)
                threading.Thread(target=run_llm_chat, daemon=True).start()
            else:
                self.add_bubble("Sorry, I didn't understand. Try using a feature button.", is_user=False)
        except Exception as e:
            logging.error(f"send_message error: {str(e)}")
            self.add_bubble(f"Critical error: {str(e)}", is_user=False)
        self.text_input.text = ''

class FarmerAgentApp(MDApp):
    def build(self):
        return ChatScreen()

if __name__ == "__main__":
    FarmerAgentApp().run()