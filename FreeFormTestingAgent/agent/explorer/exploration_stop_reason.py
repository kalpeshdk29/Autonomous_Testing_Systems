"""
File: exploration_stop_reason.py

Purpose:
    Defines the reason why an exploration session stopped.

Architecture:

Exploration Loop
        ↓
Limit Reached?
        ↓
ExplorationStopReason
        ↓
ExplorationResult
"""

from enum import Enum


class ExplorationStopReason(str, Enum):
    """
    Possible reasons for ending exploration.
    """

    COMPLETED = "COMPLETED"

    MAX_STATES_REACHED = (
        "MAX_STATES_REACHED"
    )

    MAX_ACTIONS_REACHED = (
        "MAX_ACTIONS_REACHED"
    )

    MAX_TRANSITIONS_REACHED = (
        "MAX_TRANSITIONS_REACHED"
    )

    MAX_DURATION_REACHED = (
        "MAX_DURATION_REACHED"
    )

    MAX_FAILURES_REACHED = (
        "MAX_FAILURES_REACHED"
    )