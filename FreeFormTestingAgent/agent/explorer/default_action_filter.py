"""
File: default_action_filter.py

Purpose:
    Filters dangerous or
    non-useful actions.

Architecture:

Action
    ↓
Rule Engine
    ↓
Allow / Reject
"""

from agent.explorer.action_filter import (
    ActionFilter
)


class DefaultActionFilter(
    ActionFilter
):
    """
    Default explorer action filter.
    """

    #
    # Actions that should never
    # be explored automatically.
    #
    BLOCKED_ACTIONS = {

        "",
        "Close",
        "Minimize",
        "Maximize",
        "Restore",

        "TogglePaneButton",

        "MemRecall",
        "MemPlus",
        "MemMinus",
        "memButton",
        "ClearMemoryButton",
    }

    def allow(
        self,
        action
    ) -> bool:
        """
        Check if action is allowed.
        """

        if (
            action.target
            in
            self.BLOCKED_ACTIONS
        ):
            return False

        return True