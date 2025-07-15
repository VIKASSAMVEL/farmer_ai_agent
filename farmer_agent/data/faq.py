# Offline FAQ & Guidance
# Provides frequently asked questions and best practices for common crops/issues
import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
FAQ_FILE = os.path.join(DATA_DIR, 'faq.json')

class FAQ:
    def __init__(self):
        self.faq = self.load_faq()

    def load_faq(self):
        if not os.path.exists(FAQ_FILE):
            return []
        with open(FAQ_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    def search(self, query):
        results = [item for item in self.faq if query.lower() in item['question'].lower()]
        return results

    def get_all(self):
        return self.faq

if __name__ == "__main__":
    faq = FAQ()
    print(faq.get_all())
    print(faq.search('tomato'))
