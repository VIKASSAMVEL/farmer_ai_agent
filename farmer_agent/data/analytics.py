# Basic Data Analytics (Offline)
# Summarizes user activity, crop trends, and advisory effectiveness
import json
import os
from collections import Counter

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
HISTORY_FILE = os.path.join(DATA_DIR, 'user_history.json')

class Analytics:
    def __init__(self):
        self.data = self.load_history()

    def load_history(self):
        if not os.path.exists(HISTORY_FILE):
            return {}
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    def user_activity_summary(self, username):
        user = self.data.get(username, {})
        queries = user.get('queries', [])
        return {
            'total_queries': len(queries),
            'last_query': queries[-1] if queries else None
        }

    def crop_trends(self):
        crops = []
        for user in self.data.values():
            for q in user.get('queries', []):
                crop = q['query'].split(',')[0].strip()
                crops.append(crop)
        return Counter(crops)

    def advisory_effectiveness(self, username):
        # Placeholder: could be expanded with feedback tracking
        user = self.data.get(username, {})
        queries = user.get('queries', [])
        return {
            'advisories_given': len(queries)
        }

if __name__ == "__main__":
    analytics = Analytics()
    print("User activity summary for 'farmer1':", analytics.user_activity_summary('farmer1'))
    print("Crop trends:", analytics.crop_trends())
    print("Advisory effectiveness for 'farmer1':", analytics.advisory_effectiveness('farmer1'))
