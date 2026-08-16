from ai.models import AIResult, TaskStep
from ai.goal_detector import GoalDetector
from ai.task_planner import TaskPlanner


class AIDecisionEngine:
    """
    ACCESS Phase 5 AI / Decision Layer.

    Responsibilities:
    - Interpret natural-language commands
    - Detect goals
    - Detect compound workflows
    - Produce AIResult objects
    - Produce ordered TaskStep objects
    - Never execute system actions directly
    """

    CONFIDENCE_THRESHOLD = 0.6

    def __init__(self):
        self.goal_detector = GoalDetector()
        self.task_planner = TaskPlanner()

    def interpret(self, text: str, recent_memory=None) -> AIResult:
        """
        Convert natural-language input into an AIResult.

        Example:

            please open calculator

        becomes:

            AIResult(
                intent="open_application",
                target="Calculator",
                ...
            )
        """

        cleaned = (text or "").strip()

        if not cleaned:
            return AIResult(
                intent="unknown",
                target=None,
                confidence=0.0,
                steps=[],
                raw_input=cleaned,
            )

        # -------------------------------------------------
        # MULTI-STEP TASK
        # -------------------------------------------------

        planned_steps = self.task_planner.plan(cleaned)

        if planned_steps:
            return AIResult(
                intent="multi_step_plan",
                target=None,
                confidence=0.85,
                steps=list(planned_steps),
                raw_input=cleaned,
            )

        # -------------------------------------------------
        # SINGLE-STEP GOAL DETECTION
        # -------------------------------------------------

        intent, target, confidence = (
            self.goal_detector.detect(cleaned)
        )

        # -------------------------------------------------
        # MEMORY-AWARE FALLBACK
        # -------------------------------------------------

        if (
            intent == "unknown"
            and recent_memory
            and self._is_vague_reference(cleaned)
        ):
            try:
                previous_input = recent_memory[0][0]
            except (IndexError, TypeError):
                previous_input = None

            if previous_input:
                (
                    previous_intent,
                    previous_target,
                    previous_confidence,
                ) = self.goal_detector.detect(
                    previous_input
                )

                if previous_intent != "unknown":
                    intent = previous_intent
                    target = previous_target

                    # Inferred commands receive lower confidence.
                    confidence = max(
                        previous_confidence - 0.2,
                        0.0,
                    )

        # -------------------------------------------------
        # STRUCTURED RESULT
        # -------------------------------------------------

        steps = []

        if intent != "unknown":
            steps.append(
                TaskStep(
                    action=intent,
                    target=target,
                )
            )

        return AIResult(
            intent=intent,
            target=target,
            confidence=confidence,
            steps=steps,
            raw_input=cleaned,
        )

    @staticmethod
    def _is_vague_reference(text: str) -> bool:
        """Detect simple references to the previous task."""

        phrases = {
            "do that again",
            "same as before",
            "repeat that",
            "again",
        }

        return text.strip().lower() in phrases