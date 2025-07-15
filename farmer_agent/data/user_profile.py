
# User History & Profiling (Offline)
# Multi-user support: switch and manage multiple user profiles
import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
HISTORY_FILE = os.path.join(DATA_DIR, 'user_history.json')

class UserProfile:
    def __init__(self, username):
        self.username = username
        self.history = self.load_history()

    def load_history(self):
        if not os.path.exists(HISTORY_FILE):
            return {}
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get(self.username, {})

    def save_history(self):
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {}
        data[self.username] = self.history
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_query(self, query, advisory):
        if 'queries' not in self.history:
            self.history['queries'] = []
        self.history['queries'].append({'query': query, 'advisory': advisory})
        self.save_history()

    def get_last_advisory(self):
        if 'queries' in self.history and self.history['queries']:
            return self.history['queries'][-1]['advisory']
        return None

class UserManager:
    def __init__(self):
        self.users = self.load_users()
        self.current_user = None

    def load_users(self):
        if not os.path.exists(HISTORY_FILE):
            return []
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return list(data.keys())

    def switch_user(self, username):
        self.current_user = UserProfile(username)
        return self.current_user

    def list_users(self):
        return self.load_users()

    def add_user(self, username):
        if username not in self.list_users():
            user = UserProfile(username)
            user.save_history()
        return username

if __name__ == "__main__":
    manager = UserManager()
    print("Existing users:", manager.list_users())
    username = input("Enter username to switch or create: ")
    manager.add_user(username)
    user = manager.switch_user(username)
    user.add_query('Tomato, Sandy Loam', {'advice': 'Sample advisory'})
    print(user.get_last_advisory())
