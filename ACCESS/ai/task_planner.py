from ai.models import TaskStep


class TaskPlanner:
    """
    Creates ordered execution plans for compound commands.
    """

    WORKSPACE_PRESETS = {
        "development workspace": [
            TaskStep(
                action="open_application",
                target="Visual Studio Code",
            ),
            TaskStep(
                action="open_application",
                target="Terminal",
            ),
            TaskStep(
                action="open_application",
                target="Google Chrome",
            ),
        ],

        "writing workspace": [
            TaskStep(
                action="open_application",
                target="Notes",
            ),
            TaskStep(
                action="open_application",
                target="Google Chrome",
            ),
        ],
    }

    def plan(self, text: str):
        cleaned = (text or "").strip().lower()

        for key, steps in self.WORKSPACE_PRESETS.items():

            if key in cleaned:
                return [
                    TaskStep(
                        action=step.action,
                        target=step.target,
                    )
                    for step in steps
                ]

        return []