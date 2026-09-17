import unittest
from core.engine import AccessEngine


class EngineIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = AccessEngine()

    def test_status_command(self):
        res = self.engine.process("status")
        self.assertIn("ACCESS STATUS", res)
        self.assertIn("ONLINE", res)

    def test_help_command(self):
        res = self.engine.process("help")
        self.assertIn("ACCESS Command Reference", res)
        self.assertIn("General Commands", res)

    def test_system_health_and_metrics(self):
        health = self.engine.process("system health")
        self.assertIn("System Health & Performance Monitor", health)
        self.assertIn("CPU Load", health)
        self.assertIn("Memory", health)

        cpu = self.engine.process("cpu")
        self.assertIn("CPU Utilization", cpu)

        battery = self.engine.process("battery")
        self.assertTrue("Battery" in battery or "Desktop" in battery)

    def test_demo_command(self):
        res = self.engine.process("demo")
        self.assertIn("ACCESS Live Demonstration Showcase", res)
        self.assertIn("Architectural Pillars", res)

    def test_date_and_time(self):
        time_res = self.engine.process("what time is it")
        self.assertIn("It's ", time_res)

        date_res = self.engine.process("what is today's date")
        self.assertIn("Today is ", date_res)

        day_res = self.engine.process("what day is today")
        self.assertIn("Today is ", day_res)

    def test_safe_math(self):
        res = self.engine.process("calculate 25 * 40")
        self.assertEqual(res, "25 * 40 = 1,000")

        res = self.engine.process("what is 100 / 4")
        self.assertEqual(res, "100 / 4 = 25")

        res = self.engine.process("solve 2 ^ 8")
        self.assertEqual(res, "2 ^ 8 = 256")

    def test_smart_home_commands(self):
        toggle_res = self.engine.process("turn on living room light")
        self.assertIn("Living Room Light", toggle_res)

        temp_res = self.engine.process("set thermostat to 21")
        self.assertIn("21°C", temp_res)

        home_status = self.engine.process("smart home")
        self.assertIn("ACCESS Smart Home & Security Operating System", home_status)

    def test_reminder_command(self):
        res = self.engine.process("remind me in 10 minutes to test audio")
        self.assertIn("Reminder", res)
        self.assertIn("test audio", res)

        list_res = self.engine.process("show reminders")
        self.assertIn("test audio", list_res)

    def test_conversational_fallback(self):
        res = self.engine.process("hello")
        self.assertTrue(any(w in res.lower() for w in ["hello", "greetings", "hi", "companion", "assist"]))

        joke = self.engine.process("tell me a joke")
        self.assertTrue(len(joke) > 10)

        about = self.engine.process("who are you")
        self.assertIn("ACCESS", about)


if __name__ == "__main__":
    unittest.main()
