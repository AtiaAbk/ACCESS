"""Cross-platform, read-only system monitoring for the ACCESS dashboard."""

from __future__ import annotations

import os
import platform
import socket
import threading
import time
from dataclasses import dataclass

import psutil


@dataclass(frozen=True)
class SystemSnapshot:
    cpu_percent: float
    memory_percent: float
    memory_used: int
    memory_total: int
    disk_percent: float
    disk_used: int
    disk_total: int
    battery_percent: float | None
    battery_plugged: bool | None
    battery_seconds_left: int | None
    network_download_rate: float
    network_upload_rate: float
    network_received: int
    network_sent: int
    device_name: str
    os_version: str
    uptime_seconds: int
    local_ip: str
    warnings: tuple[str, ...]
    sampled_at: float


class SystemMonitor:
    """Collect system metrics without changing operating-system state."""

    CPU_WARNING = 90
    MEMORY_WARNING = 90
    DISK_WARNING = 90
    BATTERY_WARNING = 15

    def __init__(self):
        self._lock = threading.Lock()
        counters = psutil.net_io_counters()
        self._last_network = (
            counters.bytes_recv if counters else 0,
            counters.bytes_sent if counters else 0,
            time.monotonic(),
        )

    def snapshot(self) -> SystemSnapshot:
        """Return one coherent sample; safe to call from a worker thread."""

        cpu_percent = float(psutil.cpu_percent(interval=0.15))
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(self._disk_root())
        battery = psutil.sensors_battery()
        network = psutil.net_io_counters()
        now = time.monotonic()

        received = network.bytes_recv if network else 0
        sent = network.bytes_sent if network else 0
        with self._lock:
            previous_received, previous_sent, previous_time = self._last_network
            elapsed = max(0.001, now - previous_time)
            download_rate = max(0.0, (received - previous_received) / elapsed)
            upload_rate = max(0.0, (sent - previous_sent) / elapsed)
            self._last_network = received, sent, now

        battery_percent = float(battery.percent) if battery else None
        battery_plugged = battery.power_plugged if battery else None
        seconds_left = None
        if battery and battery.secsleft not in {
            psutil.POWER_TIME_UNKNOWN,
            psutil.POWER_TIME_UNLIMITED,
        }:
            seconds_left = max(0, int(battery.secsleft))

        warnings = self.build_warnings(
            cpu_percent=cpu_percent,
            memory_percent=float(memory.percent),
            disk_percent=float(disk.percent),
            battery_percent=battery_percent,
            battery_plugged=battery_plugged,
        )
        return SystemSnapshot(
            cpu_percent=cpu_percent,
            memory_percent=float(memory.percent),
            memory_used=int(memory.used),
            memory_total=int(memory.total),
            disk_percent=float(disk.percent),
            disk_used=int(disk.used),
            disk_total=int(disk.total),
            battery_percent=battery_percent,
            battery_plugged=battery_plugged,
            battery_seconds_left=seconds_left,
            network_download_rate=download_rate,
            network_upload_rate=upload_rate,
            network_received=received,
            network_sent=sent,
            device_name=socket.gethostname() or "Unknown device",
            os_version=f"{platform.system()} {platform.release()}",
            uptime_seconds=max(0, int(time.time() - psutil.boot_time())),
            local_ip=self._local_ip(),
            warnings=warnings,
            sampled_at=time.time(),
        )

    @classmethod
    def build_warnings(
        cls,
        *,
        cpu_percent: float,
        memory_percent: float,
        disk_percent: float,
        battery_percent: float | None,
        battery_plugged: bool | None,
    ) -> tuple[str, ...]:
        warnings: list[str] = []
        if cpu_percent >= cls.CPU_WARNING:
            warnings.append(f"CPU usage is high ({cpu_percent:.0f}%).")
        if memory_percent >= cls.MEMORY_WARNING:
            warnings.append(f"Memory usage is high ({memory_percent:.0f}%).")
        if disk_percent >= cls.DISK_WARNING:
            warnings.append(f"Storage is almost full ({disk_percent:.0f}% used).")
        if (
            battery_percent is not None
            and battery_percent <= cls.BATTERY_WARNING
            and not battery_plugged
        ):
            warnings.append(f"Battery is low ({battery_percent:.0f}%). Connect power soon.")
        return tuple(warnings)

    @staticmethod
    def _disk_root() -> str:
        if platform.system() == "Windows":
            return os.environ.get("SystemDrive", "C:") + "\\"
        return "/"

    @staticmethod
    def _local_ip() -> str:
        try:
            addresses = socket.getaddrinfo(
                socket.gethostname(),
                None,
                family=socket.AF_INET,
                type=socket.SOCK_STREAM,
            )
            for address in addresses:
                candidate = address[4][0]
                if not candidate.startswith("127."):
                    return candidate
        except OSError:
            pass
        return "Unavailable"


def format_bytes(value: float) -> str:
    """Format a byte value using compact binary units."""

    size = max(0.0, float(value))
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def format_duration(seconds: int | None) -> str:
    if seconds is None:
        return "Unknown"
    days, remainder = divmod(max(0, int(seconds)), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes = remainder // 60
    if days:
        return f"{days}d {hours}h {minutes}m"
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"
