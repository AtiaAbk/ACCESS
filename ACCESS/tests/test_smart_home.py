import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from plugins.smart_home import SmartHomeHub


class SmartHomeHubTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.storage_path = Path(self.temp_dir.name) / "smart_home.json"
        self.hub = SmartHomeHub(storage_path=self.storage_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_default_devices_initialized(self):
        self.assertIn("living_room_light", self.hub.devices)
        self.assertIn("thermostat", self.hub.devices)
        self.assertIn("front_door_lock", self.hub.devices)
        self.assertIn("cctv_living_room", self.hub.devices)

    def test_toggle_light(self):
        res = self.hub.handle_command("turn on living room light")
        self.assertIn("Living Room Light is now turned ON", res)
        self.assertTrue(self.hub.devices["living_room_light"].state)

        res = self.hub.handle_command("turn off living room light")
        self.assertIn("Living Room Light is now turned OFF", res)
        self.assertFalse(self.hub.devices["living_room_light"].state)

    def test_set_thermostat(self):
        res = self.hub.handle_command("set thermostat to 20")
        self.assertIn("20°C", res)
        self.assertEqual(self.hub.devices["thermostat"].attributes["target_temp"], 20)

    def test_security_arming_and_disarming(self):
        res = self.hub.handle_command("arm security away")
        self.assertIn("ARMED (Away Mode)", res)
        self.assertEqual(self.hub.security_mode, "Away")
        self.assertTrue(self.hub.devices["front_door_lock"].state)

        res = self.hub.handle_command("disarm security")
        self.assertIn("DISARMED", res)
        self.assertEqual(self.hub.security_mode, "Disarmed")

    def test_emergency_alarm(self):
        res = self.hub.handle_command("trigger alarm")
        self.assertIn("EMERGENCY SIREN TRIGGERED", res)
        self.assertTrue(self.hub.alarm_active)

    def test_door_lock_unlock(self):
        res = self.hub.handle_command("unlock front door")
        self.assertIn("unlocked", res)
        self.assertFalse(self.hub.devices["front_door_lock"].state)

        res = self.hub.handle_command("lock front door")
        self.assertIn("locked", res)
        self.assertTrue(self.hub.devices["front_door_lock"].state)

    def test_summary_reports(self):
        summary = self.hub.get_summary()
        self.assertIn("ACCESS Smart Home & Security Operating System", summary)
        self.assertIn("Living Room", summary)

        sec_summary = self.hub.get_security_summary()
        self.assertIn("Intelligent Security System Status", sec_summary)


if __name__ == "__main__":
    unittest.main()
