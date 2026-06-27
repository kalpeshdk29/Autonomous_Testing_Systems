from core.models.action import (
    Action,
    ActionType
)

from core.models.ui_control import UIControl


class ActionDiscovery:

    def discover(
            self,
            controls: list[UIControl]
    ) -> list[Action]:

        actions = []

        for control in controls:

            # Clickable controls
            if control.control_type in [
                "ButtonControl",
                "HyperlinkControl",
                "MenuItemControl"
            ]:

                actions.append(
                    Action(
                        action_type=ActionType.CLICK,
                        target=control.automation_id,
                        description=f"Click '{control.name}'"
                    )
                )

        return actions