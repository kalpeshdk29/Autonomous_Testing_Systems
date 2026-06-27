"""
File: action_executor.py

Purpose:
    Execute Action objects against the target application.

Architecture:

Action
    ↓
ActionExecutor
    ↓
UI Automation
    ↓
Application
"""

import time
import uiautomation as auto

from core.models.action import Action
from core.models.action import ActionType


class ActionExecutor:
    """
    Executes Action objects on the target application.

    Responsibilities:
        - Locate target controls
        - Execute actions
        - Report success/failure
    """

    def execute(
            self,
            window,
            action: Action
    ) -> bool:
        """
        Execute a single action.

        Args:
            window:
                Target application window.

            action:
                Action to execute.

        Returns:
            True if action executed successfully.
        """

        try:

            # Currently we only support CLICK actions
            if action.action_type == ActionType.CLICK:

                return self._click(
                    window,
                    action.target
                )

            return False

        except Exception as e:

            print(
                f"Execution failed: {e}"
            )

            return False

    def _click(
            self,
            window,
            automation_id: str
    ) -> bool:
        """
        Click a UI element by AutomationId.

        Args:
            window:
                Target application window.

            automation_id:
                AutomationId of the control.

        Returns:
            True if click succeeded.
        """

        # Find target control
        control = window.Control(
            AutomationId=automation_id
        )

        # Verify control exists
        if not control.Exists():

            print(
                f"Control not found: "
                f"{automation_id}"
            )

            return False

        print(
            f"Clicking: "
            f"{automation_id}"
        )

        # Perform click
        control.Click()

        # Give UI time to update
        time.sleep(0.5)

        return True