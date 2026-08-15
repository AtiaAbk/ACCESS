from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from app.reminders import ReminderService


class ReminderServiceTests(TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.path = Path(self.temporary.name) / "reminders.json"
        self.service = ReminderService(self.path)
        self.now = datetime(2026, 8, 14, 10, 0, 0)

    def tearDown(self):
        self.temporary.cleanup()

    def test_relative_reminder_is_persisted_and_becomes_due(self):
        response = self.service.interpret(
            "remind me in 10 minutes to call Atia",
            now=self.now,
        )
        self.assertIn("call Atia", response)
        restored = ReminderService(self.path)
        self.assertIn("call Atia", restored.describe())
        self.assertEqual([], restored.due_reminders(self.now + timedelta(minutes=9)))
        due = restored.due_reminders(self.now + timedelta(minutes=10))
        self.assertEqual("call Atia", due[0].message)
        self.assertEqual("You have no scheduled reminders.", restored.describe())

    def test_clock_reminder_rolls_to_tomorrow(self):
        response = self.service.interpret(
            "remind me at 9:30 am to send the report",
            now=self.now,
        )
        self.assertIn("Aug 15 at 09:30 AM", response)

    def test_cancel_reminder(self):
        self.service.interpret("remind me in 1 hour to stretch", now=self.now)
        reminder_id = self.service._reminders[0].id
        response = self.service.interpret(f"cancel reminder {reminder_id}")
        self.assertIn("was cancelled", response)
        self.assertEqual("You have no scheduled reminders.", self.service.describe())

    def test_unrelated_text_is_not_claimed(self):
        self.assertIsNone(self.service.interpret("tell me about reminders"))
