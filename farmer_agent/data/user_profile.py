
# User History & Profiling (Offline)
# Multi-user support: switch and manage multiple user profiles

import json
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
HISTORY_FILE = os.path.join(DATA_DIR, 'user_history.json')


class UserProfile:
    def __init__(self, username):
        self.username = username
        self.history = self.load_history()
        self._init_metadata()

    def _init_metadata(self):
        now = datetime.utcnow().isoformat()
        if 'meta' not in self.history:
            self.history['meta'] = {
                'created_at': now,
                'last_active': now
            }
        else:
            self.history['meta']['last_active'] = now
        if 'queries' not in self.history:
            self.history['queries'] = []

    def load_history(self):
        if not os.path.exists(HISTORY_FILE):
            return {}
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get(self.username, {})
        except Exception:
            return {}

    def save_history(self):
        # Robust to file corruption and concurrent writes
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {}
        except Exception:
            data = {}
        data[self.username] = self.history
        tmp_file = HISTORY_FILE + ".tmp"
        with open(tmp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_file, HISTORY_FILE)

    def add_query(self, query, advisory):
        self._init_metadata()
        self.history['queries'].append({
            'query': query,
            'advisory': advisory,
            'timestamp': datetime.utcnow().isoformat()
        })
        self.save_history()

    def get_last_advisory(self):
        if 'queries' in self.history and self.history['queries']:
            return self.history['queries'][-1]['advisory']
        return None

    def get_all_queries(self):
        return self.history.get('queries', [])

    def clear_history(self):
        self.history['queries'] = []
        self._init_metadata()
        self.save_history()

    def get_metadata(self):
        return self.history.get('meta', {})


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
        if self.current_user:
            self.current_user._init_metadata()
            self.current_user.save_history()
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
    print("Last advisory:", user.get_last_advisory())
    print("All queries:", user.get_all_queries())
    print("User metadata:", user.get_metadata())
