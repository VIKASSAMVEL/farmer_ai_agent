# Basic Data Analytics (Offline)
# Summarizes user activity, crop trends, and advisory effectiveness
import json
import os
from collections import Counter

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
HISTORY_FILE = os.path.join(DATA_DIR, 'user_history.json')

class Analytics:
    def feedback_trends(self, username=None):
        """
        Returns feedback trends over time (positive/negative counts by date).
        If username is None, aggregates for all users.
        """
        from collections import defaultdict
        import datetime
        trends = defaultdict(lambda: {'positive': 0, 'negative': 0})
        users = [username] if username else self.data.keys()
        for user in users:
            user_data = self.data.get(user, {})
            for q in user_data.get('queries', []):
                feedback = q.get('feedback') or (q.get('advisory', {}) if isinstance(q.get('advisory'), dict) else {}).get('feedback')
                date = q.get('date')
                if not date:
                    date = q.get('timestamp') if 'timestamp' in q else None
                if not date:
                    date = 'unknown'
                else:
                    try:
                        # Normalize to YYYY-MM-DD
                        date = str(date)[:10]
                    except Exception:
                        date = str(date)
                if feedback == 'positive':
                    trends[date]['positive'] += 1
                elif feedback == 'negative':
                    trends[date]['negative'] += 1
        return dict(trends)

    def most_queried_crops(self, top_n=5):
        """
        Returns the most frequently queried crops across all users.
        """
        crop_counter = self.crop_trends()
        return crop_counter.most_common(top_n)

    def user_engagement(self):
        """
        Returns a summary of user engagement: total users, active users (with queries), and average queries per user.
        """
        total_users = len(self.data)
        active_users = sum(1 for u in self.data.values() if u.get('queries'))
        total_queries = sum(len(u.get('queries', [])) for u in self.data.values())
        avg_queries = total_queries / total_users if total_users else 0
        return {
            'total_users': total_users,
            'active_users': active_users,
            'average_queries_per_user': avg_queries
        }

    def feedback_by_crop(self):
        """
        Returns feedback breakdown (positive/negative) for each crop.
        """
        from collections import defaultdict
        crop_feedback = defaultdict(lambda: {'positive': 0, 'negative': 0})
        for user in self.data.values():
            for q in user.get('queries', []):
                crop = q['query'].split(',')[0].strip()
                feedback = q.get('feedback') or (q.get('advisory', {}) if isinstance(q.get('advisory'), dict) else {}).get('feedback')
                if feedback == 'positive':
                    crop_feedback[crop]['positive'] += 1
                elif feedback == 'negative':
                    crop_feedback[crop]['negative'] += 1
        return dict(crop_feedback)
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
        """
        Returns effectiveness metrics for advisories given to a user.
        Tracks positive/negative feedback if available in user history.
        """
        user = self.data.get(username, {})
        queries = user.get('queries', [])
        # Feedback tracking: expects each query to have a 'feedback' field ("positive"/"negative")
        positive = 0
        negative = 0
        for q in queries:
            feedback = q.get('feedback')
            if feedback == 'positive':
                positive += 1
            elif feedback == 'negative':
                negative += 1
        total = len(queries)
        effectiveness = (positive / total) if total else None
        return {
            'advisories_given': total,
            'positive_feedback': positive,
            'negative_feedback': negative,
            'effectiveness_ratio': effectiveness
        }

if __name__ == "__main__":
    analytics = Analytics()
    print("User activity summary for 'farmer1':", analytics.user_activity_summary('farmer1'))
    print("Crop trends:", analytics.crop_trends())
    print("Advisory effectiveness for 'farmer1':", analytics.advisory_effectiveness('farmer1'))
