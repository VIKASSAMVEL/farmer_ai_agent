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
        self.size_hint_y = None
        self.height = self.texture_size[1] + 20
        self.halign = 'right' if is_user else 'left'
        self.color = (0,0,0,1) if is_user else (0.1,0.5,0.1,1)
        self.text_size = (self.width, None)

class ChatScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.chat_history = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.chat_history.bind(minimum_height=self.chat_history.setter('height'))  # type: ignore
        self.scroll = ScrollView(size_hint=(1, 0.9))
        self.scroll.add_widget(self.chat_history)
        self.add_widget(self.scroll)

        self.input_box = BoxLayout(size_hint=(1, 0.1))
        self.text_input = TextInput(hint_text='Type your message...', multiline=False)
        self.send_btn = Button(text='Send')
        self.send_btn.bind(on_press=self.send_message)  # type: ignore
        self.input_box.add_widget(self.text_input)
        self.input_box.add_widget(self.send_btn)
        self.add_widget(self.input_box)

    def send_message(self, instance):
        user_text = self.text_input.text.strip()
        if user_text:
            self.add_bubble(user_text, is_user=True)
            # Here, integrate with backend logic to get agent response
            agent_response = self.get_agent_response(user_text)
            self.add_bubble(agent_response, is_user=False)
            self.text_input.text = ''

    def add_bubble(self, text, is_user=False):
        bubble = ChatBubble(text, is_user=is_user)
        self.chat_history.add_widget(bubble)
        self.scroll.scroll_y = 0

    def get_agent_response(self, user_text):
        # Placeholder: integrate with Farmer Agent backend
        return f"You said: {user_text} (response here)"

class FarmerAgentApp(App):
    def build(self):
        return ChatScreen()

if __name__ == '__main__':
    FarmerAgentApp().run()
