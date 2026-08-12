from ai.models import TaskStep


class TaskPlanner:
    """Breaks compound/abstract requests into ordered TaskStep plans."""

    WORKSPACE_PRESETS = {
        "development workspace": [
            TaskStep(action="open_application", target="VS Code"),
            TaskStep(action="open_application", target="Terminal"),
            TaskStep(action="open_application", target="browser"),
        ],
        "writing workspace": [
            TaskStep(action="open_application", target="Notes"),
            TaskStep(action="open_application", target="browser"),
        ],
    }

    def plan(self, text: str):
        """Return a list of TaskStep if the request matches a known compound
        workflow, otherwise an empty list (meaning: not multi-step)."""

        cleaned = text.strip().lower()

        for key, steps in self.WORKSPACE_PRESETS.items():
            if key in cleaned:
                return steps

        return []