from unittest import TestCase

from app.system_monitor import SystemMonitor, format_bytes, format_duration


class SystemMonitorTests(TestCase):
    def test_warning_thresholds(self):
        warnings = SystemMonitor.build_warnings(
            cpu_percent=95,
            memory_percent=91,
            disk_percent=93,
            battery_percent=10,
            battery_plugged=False,
        )
        self.assertEqual(4, len(warnings))
        self.assertTrue(any("CPU" in warning for warning in warnings))
        self.assertTrue(any("Battery" in warning for warning in warnings))

    def test_charging_battery_does_not_warn(self):
        warnings = SystemMonitor.build_warnings(
            cpu_percent=10,
            memory_percent=20,
            disk_percent=30,
            battery_percent=5,
            battery_plugged=True,
        )
        self.assertEqual((), warnings)

    def test_formatters(self):
        self.assertEqual("1.0 KB", format_bytes(1024))
        self.assertEqual("1h 30m", format_duration(5400))
        self.assertEqual("1d 2h 0m", format_duration(93600))

    def test_live_snapshot_has_valid_core_metrics(self):
        snapshot = SystemMonitor().snapshot()
        self.assertGreaterEqual(snapshot.cpu_percent, 0)
        self.assertLessEqual(snapshot.cpu_percent, 100)
        self.assertGreater(snapshot.memory_total, 0)
        self.assertGreater(snapshot.disk_total, 0)
        self.assertTrue(snapshot.device_name)
        self.assertTrue(snapshot.os_version)
        self.assertGreaterEqual(snapshot.uptime_seconds, 0)
