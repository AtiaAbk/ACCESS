from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TaskStep:
    """One atomic step inside a multi-step plan."""
    action: str
    target: Optional[str] = None


@dataclass
class AIResult:
    """Structured output of the AI interpretation layer."""
    intent: str
    target: Optional[str] = None
    confidence: float = 0.0
    steps: List[TaskStep] = field(default_factory=list)
    raw_input: str = ""

    def is_multi_step(self) -> bool:
        return len(self.steps) > 1