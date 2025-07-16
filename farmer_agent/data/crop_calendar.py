# Crop Calendar & Reminders (Offline)
# Provides crop schedules and allows setting reminders for farming activities
import json
import os
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
CALENDAR_FILE = os.path.join(DATA_DIR, 'crop_calendar.json')
REMINDER_FILE = os.path.join(DATA_DIR, 'reminders.json')

class CropCalendar:
    def next_activity(self, crop_name, from_date=None):
        """
        Return the next scheduled activity for a crop after from_date (or today).
        """
        schedule = self.get_schedule(crop_name)
        if not schedule:
            return None
        today = from_date or datetime.now().strftime('%Y-%m-%d')
        next_act = None
        next_date = None
        for activity, timing in schedule.items():
            if isinstance(timing, str):
                if timing >= today:
                    if not next_date or timing < next_date:
                        next_act, next_date = activity, timing
            elif isinstance(timing, list):
                for d in timing:
                    if d >= today:
                        if not next_date or d < next_date:
                            next_act, next_date = activity, d
        if next_act:
            return {'activity': next_act, 'date': next_date}
        return None
    def get_calendar_options(self):
        """
        Returns the available calendar options for UI button selection, matching the main UI.
        """
        return [
            ("Show crop calendar", "1"),
            ("List crops", "2"),
            ("Add reminder", "3"),
            ("Add recurring reminder", "4"),
            ("Delete reminders", "5"),
            ("Next activity", "6")
        ]
    def __init__(self):
        self.calendar = self.load_calendar()

    def load_calendar(self):
        if not os.path.exists(CALENDAR_FILE):
            return {}
        with open(CALENDAR_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_schedule(self, crop_name):
        """
        Returns the full schedule for a crop, including sowing, transplanting, fertilizing, irrigation, and harvesting.
        """
        schedule = self.calendar.get(crop_name.lower(), None)
        if not schedule:
            # Try case-insensitive match
            for k, v in self.calendar.items():
                if k.lower() == crop_name.lower():
                    schedule = v
                    break
        return schedule or {}

    def list_crops(self):
        """Return a list of all crops in the calendar."""
        return list(self.calendar.keys())

    def suggest_activities(self, crop_name, date=None):
        """
        Suggest activities for a crop on a given date (or today).
        """
        schedule = self.get_schedule(crop_name)
        if not schedule:
            return []
        today = date or datetime.now().strftime('%Y-%m-%d')
        suggestions = []
        for activity, timing in schedule.items():
            if isinstance(timing, str) and timing == today:
                suggestions.append(activity)
            elif isinstance(timing, list) and today in timing:
                suggestions.append(activity)
        return suggestions

class Reminders:
    def add_recurring_reminder(self, crop, activity, start_in_days, interval_days, occurrences):
        """
        Add a recurring reminder for a crop activity, starting after start_in_days, repeating every interval_days, for a number of occurrences.
        """
        for i in range(occurrences):
            date = (datetime.now() + timedelta(days=start_in_days + i * interval_days)).strftime('%Y-%m-%d')
            self.reminders.append({'crop': crop, 'activity': activity, 'date': date, 'recurring': True})
        self.save_reminders()

    def delete_reminder(self, crop, activity=None, date=None):
        """
        Delete reminders by crop, and optionally by activity and date.
        """
        new_reminders = []
        for r in self.reminders:
            if r['crop'].lower() != crop.lower():
                new_reminders.append(r)
            elif activity and r['activity'].lower() != activity.lower():
                new_reminders.append(r)
            elif date and r['date'] != date:
                new_reminders.append(r)
        self.reminders = new_reminders
        self.save_reminders()
    def get_reminder_options(self):
        """
        Returns the available reminder options for UI button selection (for future extensibility), matching the main UI.
        """
        return [
            ("Add reminder", "3"),
            ("Add recurring reminder", "4"),
            ("Delete reminders", "5")
        ]
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

    def search_reminders(self, crop=None, activity=None, upcoming_only=True):
        """
        Search reminders by crop, activity, and optionally only upcoming.
        """
        today = datetime.now().strftime('%Y-%m-%d')
        results = self.reminders
        if crop:
            results = [r for r in results if r['crop'].lower() == crop.lower()]
        if activity:
            results = [r for r in results if activity.lower() in r['activity'].lower()]
        if upcoming_only:
            results = [r for r in results if r['date'] >= today]
        return results

    def save_reminders(self):
        with open(REMINDER_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.reminders, f, ensure_ascii=False, indent=2)

    def get_upcoming(self):
        today = datetime.now().strftime('%Y-%m-%d')
        return [r for r in self.reminders if r['date'] >= today]

if __name__ == "__main__":
    # Demo: List all crops and their schedules
    calendar = CropCalendar()
    print("Available crops:", calendar.list_crops())
    for crop in calendar.list_crops():
        print(f"\nSchedule for {crop}:")
        print(json.dumps(calendar.get_schedule(crop), indent=2, ensure_ascii=False))

    # Demo: Suggest activities for today for Tomato
    print("\nToday's suggested activities for Tomato:")
    print(calendar.suggest_activities('Tomato'))

    # Reminders demo
    reminders = Reminders()
    reminders.add_reminder('Tomato', 'Fertilize', 7)
    reminders.add_reminder('Rice', 'Irrigate', 3)
    reminders.add_recurring_reminder('Tomato', 'Water', 1, 2, 5)
    print("\nUpcoming reminders:")
    print(reminders.get_upcoming())
    print("\nSearch reminders for Tomato:")
    print(reminders.search_reminders(crop='Tomato'))
    print("\nDeleting all reminders for Rice...")
    reminders.delete_reminder('Rice')
    print("Reminders after deletion:")
    print(reminders.get_upcoming())

    # Next activity demo
    print("\nNext scheduled activity for Tomato:")
    print(calendar.next_activity('Tomato'))
