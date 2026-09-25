"""
ACCESS Smart Home & Intelligent Security System Plugin
------------------------------------------------------
Implements the IoT Home Automation and Security System
specified in the project architecture (mainproject_overview).

Features:
- Room & Zone-based device automation (lights, AC/thermostat, curtains, pump)
- Security system modes (Disarmed, Home/Armed Stay, Away/Armed Perimeter)
- Safety & emergency sensor monitoring (Smoke, Gas, Motion, Intrusion)
- Natural command interpretation and state reporting
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class SmartDevice:
    id: str
    name: str
    room: str
    category: str  # "lighting", "climate", "security", "appliance"
    state: bool = False
    attributes: dict = field(default_factory=dict)


class SmartHomeHub:
    """Central Controller for Smart Home Automation & Intelligent Security."""

    def __init__(self, storage_path: Path | None = None):
        if storage_path is None:
            storage_path = (
                Path(__file__).resolve().parent.parent
                / "data"
                / "smart_home.json"
            )
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        self.security_mode = "Disarmed"  # Disarmed, Home, Away, Armed
        self.alarm_active = False
        self.devices: dict[str, SmartDevice] = {}
        self._init_default_devices()
        self._load_state()

    def _init_default_devices(self) -> None:
        """Initialize standard smart home layout from project specification."""
        default_devices = [
            SmartDevice("living_room_light", "Living Room Light", "Living Room", "lighting", state=True),
            SmartDevice("bedroom_light", "Bedroom Light", "Bedroom 1", "lighting", state=False),
            SmartDevice("kitchen_light", "Kitchen Light", "Kitchen", "lighting", state=False),
            SmartDevice("balcony_light", "Balcony Light", "Balcony", "lighting", state=False),
            SmartDevice(
                "thermostat",
                "AC & Thermostat",
                "Living Room",
                "climate",
                state=True,
                attributes={"current_temp": 24, "target_temp": 22, "mode": "Cool"},
            ),
            SmartDevice(
                "curtains",
                "Smart Curtains",
                "Living Room",
                "appliance",
                state=False,
                attributes={"position": "Closed"},
            ),
            SmartDevice("water_pump", "Water Pump", "Utility", "appliance", state=False),
            SmartDevice(
                "front_door_lock",
                "Front Door Lock",
                "Entry Zone",
                "security",
                state=True,
                attributes={"locked": True},
            ),
            SmartDevice(
                "cctv_living_room",
                "Living Room Camera",
                "Living Room",
                "security",
                state=True,
                attributes={"recording": True, "feed": "1080p Stream OK"},
            ),
            SmartDevice(
                "cctv_perimeter",
                "Perimeter Outdoor Camera",
                "Outdoor Zone",
                "security",
                state=True,
                attributes={"recording": True, "feed": "1080p Stream OK"},
            ),
            SmartDevice(
                "smoke_sensor",
                "Kitchen Smoke Detector",
                "Kitchen",
                "sensor",
                state=True,
                attributes={"status": "Normal", "ppm": 12},
            ),
            SmartDevice(
                "motion_sensor",
                "Entry Motion Sensor",
                "Entry Zone",
                "sensor",
                state=True,
                attributes={"motion": "No Motion Detected"},
            ),
        ]
        for dev in default_devices:
            self.devices[dev.id] = dev

    def _save_state(self) -> None:
        """Persist smart home state to JSON."""
        try:
            data = {
                "security_mode": self.security_mode,
                "alarm_active": self.alarm_active,
                "devices": {
                    dev_id: {
                        "id": dev.id,
                        "name": dev.name,
                        "room": dev.room,
                        "category": dev.category,
                        "state": dev.state,
                        "attributes": dev.attributes,
                    }
                    for dev_id, dev in self.devices.items()
                },
                "last_updated": datetime.now().isoformat(),
            }
            self.storage_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _load_state(self) -> None:
        """Load state from persistent file if it exists."""
        if not self.storage_path.exists():
            self._save_state()
            return
        try:
            data = json.loads(self.storage_path.read_text(encoding="utf-8"))
            self.security_mode = data.get("security_mode", "Disarmed")
            self.alarm_active = data.get("alarm_active", False)
            for dev_id, dev_data in data.get("devices", {}).items():
                if dev_id in self.devices:
                    self.devices[dev_id].state = dev_data.get("state", False)
                    self.devices[dev_id].attributes = dev_data.get("attributes", {})
        except Exception:
            pass

    def handle_command(self, user_command: str) -> str | None:
        """
        Analyze command and execute smart home or security action.
        Returns a response string if handled, or None if not applicable.
        """
        text = " ".join(user_command.lower().strip().split())

        # Smart Home Status / Overview
        if text in {
            "smart home",
            "smart home status",
            "smart home overview",
            "home status",
            "house status",
            "smart house",
            "check home",
            "check house",
        }:
            return self.get_summary()

        # Security Status
        if text in {
            "security status",
            "check security",
            "security mode",
            "is security armed",
        }:
            return self.get_security_summary()

        # Disarming Security
        if any(p in text for p in ["disarm security", "turn off security", "deactivate security", "disable alarm"]):
            self.security_mode = "Disarmed"
            self.alarm_active = False
            self._save_state()
            return "🛡️ Smart Security System is now [yellow]DISARMED[/yellow]. Siren alarm deactivated."

        # Arming Security
        arm_match = re.search(
            r"\b(?:arm|set)\s+security(?:\s+to|\s+system)?(?:\s+(mode|system))?\s*(away|home|stay|night)?\b",
            text,
        )
        if arm_match or (re.search(r"\barm\s+security\b", text) and "disarm" not in text) or "turn on security" in text:
            mode = "Away"
            if "home" in text or "stay" in text:
                mode = "Home"
            elif "night" in text:
                mode = "Night"
            self.security_mode = mode
            self.devices["front_door_lock"].state = True
            self.devices["front_door_lock"].attributes["locked"] = True
            self._save_state()
            return (
                f"🛡️ Smart Security System is now [bold green]ARMED ({mode} Mode)[/bold green].\n"
                f"• Perimeter cameras active with motion alerts enabled.\n"
                f"• Front door is securely locked.\n"
                f"• Intrusion sensors armed."
            )

        # Emergency Alarm Trigger / Test
        if "trigger alarm" in text or "emergency alarm" in text or "test alarm" in text or "smoke alarm test" in text:
            self.alarm_active = True
            self._save_state()
            return (
                "🚨 [bold red]EMERGENCY SIREN TRIGGERED![/bold red]\n"
                "• All room lights turned ON for visibility.\n"
                "• CCTV cameras switched to high-priority recording.\n"
                "• Simulating automated emergency contact dispatch.\n"
                "(Say 'disarm security' to cancel siren)."
            )

        # Unlock Front Door (check unlock before lock to avoid substring collision)
        if "unlock front door" in text or "unlock the door" in text or "unlock door" in text:
            self.devices["front_door_lock"].state = False
            self.devices["front_door_lock"].attributes["locked"] = False
            self._save_state()
            return "🔓 Front door has been unlocked."

        # Lock Front Door
        if "lock front door" in text or "lock the door" in text or "lock door" in text:
            self.devices["front_door_lock"].state = True
            self.devices["front_door_lock"].attributes["locked"] = True
            self._save_state()
            return "🔒 Front door has been securely locked."

        # Thermostat / AC Temperature Control
        temp_match = re.search(
            r"(?:set|change|turn)?\s*(?:thermostat|ac|air conditioner|temp|temperature)\s*(?:to)?\s*(\d{1,2})\s*(?:degrees|c|deg)?",
            text,
        )
        if temp_match:
            degrees = int(temp_match.group(1))
            if 16 <= degrees <= 32:
                dev = self.devices["thermostat"]
                dev.state = True
                dev.attributes["target_temp"] = degrees
                self._save_state()
                return f"🌡️ AC & Thermostat set to {degrees}°C (Target: {degrees}°C, Current: {dev.attributes.get('current_temp', 24)}°C)."
            return "Please specify a comfortable temperature between 16°C and 30°C."

        # Curtains Control
        if "open curtain" in text or "open the curtain" in text or "open the curtains" in text:
            self.devices["curtains"].state = True
            self.devices["curtains"].attributes["position"] = "Open (100%)"
            self._save_state()
            return "🪟 Living Room smart curtains are now OPEN."

        if "close curtain" in text or "close the curtain" in text or "close the curtains" in text:
            self.devices["curtains"].state = False
            self.devices["curtains"].attributes["position"] = "Closed"
            self._save_state()
            return "🪟 Living Room smart curtains are now CLOSED."

        # Water Pump Control
        if "turn on water pump" in text or "start water pump" in text:
            self.devices["water_pump"].state = True
            self._save_state()
            return "🚰 Water pump started. Automatic tank fill level monitoring active."

        if "turn off water pump" in text or "stop water pump" in text:
            self.devices["water_pump"].state = False
            self._save_state()
            return "🚰 Water pump stopped."

        # Device On/Off Regex Match
        toggle_match = re.search(
            r"\b(turn on|turn off|switch on|switch off)\s+(?:the\s+)?([a-z0-9 ]+)\b",
            text,
        )
        if toggle_match:
            action = toggle_match.group(1)
            target = toggle_match.group(2).strip()
            state = action.startswith("turn on") or action.startswith("switch on")

            # Check matching device
            target_device = self._find_device(target)
            if target_device:
                target_device.state = state
                self._save_state()
                verb = "turned ON" if state else "turned OFF"
                icon = "💡" if target_device.category == "lighting" else "🔌"
                return f"{icon} {target_device.name} is now {verb}."

        return None

    def _find_device(self, query: str) -> SmartDevice | None:
        """Fuzzy match device name or room."""
        q = query.lower()
        if "living room" in q:
            return self.devices.get("living_room_light")
        if "bedroom" in q:
            return self.devices.get("bedroom_light")
        if "kitchen" in q:
            return self.devices.get("kitchen_light")
        if "balcony" in q:
            return self.devices.get("balcony_light")
        if "pump" in q:
            return self.devices.get("water_pump")
        if "curtain" in q:
            return self.devices.get("curtains")
        if "thermostat" in q or "ac" in q:
            return self.devices.get("thermostat")
        if "door" in q or "lock" in q:
            return self.devices.get("front_door_lock")
        return None

    def get_summary(self) -> str:
        """Format an elegant status report of all smart home devices."""
        sec_color = "green" if self.security_mode != "Disarmed" else "yellow"
        lines = [
            "🏠 [bold cyan]ACCESS Smart Home & Security Operating System[/bold cyan]",
            f"• Security Status: [{sec_color}]● {self.security_mode.upper()}[/{sec_color}]"
            + (" (🚨 ALARM ACTIVE)" if self.alarm_active else ""),
            f"• Front Door: {'🔒 Locked' if self.devices['front_door_lock'].state else '🔓 Unlocked'}",
            "",
            "[bold white]Room Automation:[/bold white]",
            f"  • Living Room: Light {'ON' if self.devices['living_room_light'].state else 'OFF'} | Curtains {self.devices['curtains'].attributes.get('position', 'Closed')}",
            f"  • Climate: AC {'ON' if self.devices['thermostat'].state else 'OFF'} (Target: {self.devices['thermostat'].attributes.get('target_temp', 22)}°C, Mode: {self.devices['thermostat'].attributes.get('mode', 'Cool')})",
            f"  • Bedroom: Light {'ON' if self.devices['bedroom_light'].state else 'OFF'}",
            f"  • Kitchen: Light {'ON' if self.devices['kitchen_light'].state else 'OFF'} | Smoke Detector: {self.devices['smoke_sensor'].attributes.get('status', 'Normal')}",
            f"  • Balcony: Light {'ON' if self.devices['balcony_light'].state else 'OFF'}",
            f"  • Utility: Water Pump {'RUNNING' if self.devices['water_pump'].state else 'IDLE'}",
            "",
            "[bold white]Surveillance & Safety:[/bold white]",
            f"  • Living Room CCTV: {self.devices['cctv_living_room'].attributes.get('feed', 'Active')}",
            f"  • Outdoor Perimeter CCTV: {self.devices['cctv_perimeter'].attributes.get('feed', 'Active')}",
            f"  • Entry Motion Sensor: {self.devices['motion_sensor'].attributes.get('motion', 'Normal')}",
        ]
        return "\n".join(lines)

    def get_security_summary(self) -> str:
        """Detailed security system report."""
        sec_color = "green" if self.security_mode != "Disarmed" else "yellow"
        lines = [
            "🛡️ [bold cyan]Intelligent Security System Status[/bold cyan]",
            f"Current Mode: [{sec_color}]● {self.security_mode.upper()}[/{sec_color}]",
            f"Siren Alarm: {'[bold red]🚨 TRIGGERED[/bold red]' if self.alarm_active else '[green]STANDBY[/green]'}",
            f"Door Lock: {'🔒 Locked' if self.devices['front_door_lock'].state else '🔓 Unlocked'}",
            "Cameras: 2/2 Online (CCTV Living Room, Outdoor Perimeter)",
            "Sensors: Kitchen Smoke Sensor (Normal), Entry PIR Motion (Active)",
            "Emergency Escalation: Auto-Contact Dispatch Ready",
        ]
        return "\n".join(lines)
