"""Persistent reminder parsing and scheduling for ACCESS."""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path


@dataclass(frozen=True)
class Reminder:
    id: str
    message: str
    due_at: str
    created_at: str

    @property
    def due(self) -> datetime:
        return datetime.fromisoformat(self.due_at)


class ReminderService:
    """Store reminders locally and expose non-blocking due checks."""

    _RELATIVE = re.compile(
        r"^remind me in\s+(\d+)\s*(seconds?|minutes?|hours?|days?)\s+to\s+(.+)$",
        re.I,
    )
    _CLOCK = re.compile(
        r"^remind me\s+(tomorrow\s+)?at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s+to\s+(.+)$",
        re.I,
    )
    _CANCEL = re.compile(r"^(?:cancel|delete)\s+reminder\s+([a-f0-9-]+)$", re.I)

    def __init__(self, storage_path: Path):
        self.storage_path = Path(storage_path)
        self._reminders = self._load()

    def interpret(self, command: str, now: datetime | None = None) -> str | None:
        """Handle a reminder command, returning a user-facing result if matched."""

        text = " ".join(str(command or "").strip().split())
        lower = text.casefold()
        if lower in {"reminders", "show reminders", "list reminders", "my reminders"}:
            return self.describe()

        cancel_match = self._CANCEL.match(text)
        if cancel_match:
            reminder_id = cancel_match.group(1)
            if self.cancel(reminder_id):
                return f"Reminder {reminder_id} was cancelled."
            return f"I couldn't find reminder {reminder_id}."

        current = now or datetime.now()
        relative_match = self._RELATIVE.match(text)
        if relative_match:
            amount = int(relative_match.group(1))
            unit = relative_match.group(2).casefold()
            message = relative_match.group(3).strip()
            seconds = amount
            if unit.startswith("minute"):
                seconds *= 60
            elif unit.startswith("hour"):
                seconds *= 3600
            elif unit.startswith("day"):
                seconds *= 86400
            return self._create_response(message, current + timedelta(seconds=seconds), current)

        clock_match = self._CLOCK.match(text)
        if clock_match:
            tomorrow, hour_text, minute_text, meridiem, message = clock_match.groups()
            hour = int(hour_text)
            minute = int(minute_text or 0)
            if minute > 59 or hour > (12 if meridiem else 23) or hour == 0 and meridiem:
                return "That reminder time is not valid. Try a time like 6:30 PM."
            if meridiem:
                hour = hour % 12 + (12 if meridiem.casefold() == "pm" else 0)
            due = current.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if tomorrow:
                due += timedelta(days=1)
            elif due <= current:
                due += timedelta(days=1)
            return self._create_response(message.strip(), due, current)

        return None

    def _create_response(self, message: str, due: datetime, created: datetime) -> str:
        reminder = Reminder(
            id=uuid.uuid4().hex[:8],
            message=message[:500],
            due_at=due.isoformat(timespec="seconds"),
            created_at=created.isoformat(timespec="seconds"),
        )
        self._reminders.append(reminder)
        self._reminders.sort(key=lambda item: item.due)
        self._save()
        return f"Reminder {reminder.id} set for {due.strftime('%b %d at %I:%M %p')}: {reminder.message}"

    def due_reminders(self, now: datetime | None = None) -> list[Reminder]:
        current = now or datetime.now()
        due = [item for item in self._reminders if item.due <= current]
        if due:
            due_ids = {item.id for item in due}
            self._reminders = [item for item in self._reminders if item.id not in due_ids]
            self._save()
        return due

    def cancel(self, reminder_id: str) -> bool:
        normalized = reminder_id.casefold()
        remaining = [item for item in self._reminders if item.id.casefold() != normalized]
        changed = len(remaining) != len(self._reminders)
        if changed:
            self._reminders = remaining
            self._save()
        return changed

    def describe(self) -> str:
        if not self._reminders:
            return "You have no scheduled reminders."
        lines = ["Scheduled reminders:"]
        for item in sorted(self._reminders, key=lambda reminder: reminder.due):
            lines.append(
                f"• {item.id} — {item.due.strftime('%b %d, %I:%M %p')} — {item.message}"
            )
        return "\n".join(lines)

    def _load(self) -> list[Reminder]:
        try:
            payload = json.loads(self.storage_path.read_text(encoding="utf-8"))
            rows = payload if isinstance(payload, list) else []
            reminders = [Reminder(**row) for row in rows if isinstance(row, dict)]
            return sorted(reminders, key=lambda item: item.due)
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return []

    def _save(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.storage_path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps([asdict(item) for item in self._reminders], indent=2),
            encoding="utf-8",
        )
        temporary.replace(self.storage_path)
