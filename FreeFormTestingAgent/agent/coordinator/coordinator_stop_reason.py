"""
Stop reasons for autonomous continuation exploration.
"""

from enum import Enum


class CoordinatorStopReason(Enum):
    """
    Reason why ExplorationCoordinator stopped.

    NO_REMAINING_TARGETS:
        Coverage and constraints produced no expandable state
        with remaining eligible work.

    MAX_STEPS_REACHED:
        The continuation-step budget was exhausted.

    MAX_DURATION_REACHED:
        The coordinator runtime budget was exhausted.

    MAX_FAILURES_REACHED:
        Too many continuation steps failed.
    """

    NO_REMAINING_TARGETS = "NO_REMAINING_TARGETS"

    MAX_STEPS_REACHED = "MAX_STEPS_REACHED"

    MAX_DURATION_REACHED = "MAX_DURATION_REACHED"

    MAX_FAILURES_REACHED = "MAX_FAILURES_REACHED"