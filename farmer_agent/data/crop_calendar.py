# Crop Calendar & Reminders (Offline)
# Provides crop schedules and allows setting reminders for farming activities
import json
import os
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
CALENDAR_FILE = os.path.join(DATA_DIR, 'crop_calendar.json')
REMINDER_FILE = os.path.join(DATA_DIR, 'reminders.json')

class CropCalendar:
    def __init__(self):
        self.calendar = self.load_calendar()

    def load_calendar(self):
        if not os.path.exists(CALENDAR_FILE):
            return {}
        with open(CALENDAR_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_schedule(self, crop_name):
        return self.calendar.get(crop_name, {})

class Reminders:
    def __init__(self):
        self.reminders = self.load_reminders()

    def load_reminders(self):
        if not os.path.exists(REMINDER_FILE):
            return []
        with open(REMINDER_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    def add_reminder(self, crop, activity, days_from_now):
        date = (datetime.now() + timedelta(days=days_from_now)).strftime('%Y-%m-%d')
        self.reminders.append({'crop': crop, 'activity': activity, 'date': date})
        self.save_reminders()

    def save_reminders(self):
        with open(REMINDER_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.reminders, f, ensure_ascii=False, indent=2)

    def get_upcoming(self):
        today = datetime.now().strftime('%Y-%m-%d')
        return [r for r in self.reminders if r['date'] >= today]

if __name__ == "__main__":
    # Example crop calendar
    calendar = CropCalendar()
    print(calendar.get_schedule('Tomato'))
    # Example reminders
    reminders = Reminders()
    reminders.add_reminder('Tomato', 'Fertilize', 7)
    print(reminders.get_upcoming())
