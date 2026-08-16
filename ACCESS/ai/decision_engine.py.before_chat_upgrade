from ai.models import AIResult, TaskStep
from ai.goal_detector import GoalDetector
from ai.task_planner import TaskPlanner


class AIDecisionEngine:
    """
    ACCESS AI Decision Layer.

    Responsibilities:
    - Natural-language goal detection
    - Compound task planning
    - LLM result integration
    - Memory-aware interpretation
    - Structured AIResult generation

    This class NEVER executes system actions.
    """

    CONFIDENCE_THRESHOLD = 0.60

    def __init__(self, local_llm=None):
        self.goal_detector = GoalDetector()
        self.task_planner = TaskPlanner()
        self.local_llm = local_llm

    def interpret(
        self,
        text: str,
        recent_memory=None,
    ) -> AIResult:

        cleaned = (text or "").strip()

        if not cleaned:
            return AIResult(
                intent="unknown",
                confidence=0.0,
                raw_input=cleaned,
            )

        # --------------------------------------------------
        # 1. Known compound workflow
        # --------------------------------------------------

        planned_steps = self.task_planner.plan(cleaned)

        if planned_steps:
            return AIResult(
                intent="multi_step_plan",
                confidence=0.95,
                steps=planned_steps,
                raw_input=cleaned,
            )

        # --------------------------------------------------
        # 2. Deterministic local detector
        # --------------------------------------------------

        intent, target, confidence = (
            self.goal_detector.detect(cleaned)
        )

        # --------------------------------------------------
        # 3. Local LLM fallback
        # --------------------------------------------------

        llm_data = None

        if (
            intent == "unknown"
            and self.local_llm is not None
        ):
            try:
                if self.local_llm.is_available():
                    llm_data = self.local_llm.interpret(
                        cleaned
                    )
            except Exception:
                llm_data = None

        if isinstance(llm_data, dict):

            llm_intent = llm_data.get(
                "intent",
                "unknown",
            )

            llm_target = llm_data.get(
                "target"
            )

            llm_response = llm_data.get(
                "response"
            )

            if llm_intent not in {
                "",
                None,
                "unknown",
            }:

                intent = llm_intent
                target = llm_target

                confidence = max(
                    confidence,
                    0.80,
                )

                if llm_intent == "conversation":
                    return AIResult(
                        intent="conversation",
                        target=llm_target,
                        confidence=confidence,
                        response=llm_response,
                        raw_input=cleaned,
                    )

        # --------------------------------------------------
        # 4. Memory-aware "again" behaviour
        # --------------------------------------------------

        if (
            intent == "unknown"
            and recent_memory
            and self._is_vague_reference(cleaned)
        ):
            try:
                previous_input = recent_memory[0][0]
            except (
                IndexError,
                TypeError,
                KeyError,
            ):
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

                    confidence = max(
                        previous_confidence - 0.20,
                        0.0,
                    )

        # --------------------------------------------------
        # 5. Structured task step
        # --------------------------------------------------

        steps = []

        if intent not in {
            "unknown",
            "conversation",
        }:
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

        return text.strip().lower() in {
            "do that again",
            "same as before",
            "repeat that",
            "again",
        }