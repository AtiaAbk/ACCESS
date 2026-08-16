from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TaskStep:
    """One atomic step inside a multi-step plan."""

    action: str
    target: Optional[str] = None


@dataclass
class AIResult:
    """Structured result produced by the ACCESS AI layer."""

    intent: str
    target: Optional[str] = None
    confidence: float = 0.0

    steps: List[TaskStep] = field(
        default_factory=list
    )

    raw_input: str = ""

    response: Optional[str] = None

    requires_permission: bool = False

    metadata: dict = field(
        default_factory=dict
    )

    def is_multi_step(self) -> bool:
        return len(self.steps) > 1

    def is_conversation(self) -> bool:
        return self.intent == "conversation"

    def is_action(self) -> bool:
        return (
            self.intent not in {
                "conversation",
                "unknown",
            }
            and bool(self.intent)
        )