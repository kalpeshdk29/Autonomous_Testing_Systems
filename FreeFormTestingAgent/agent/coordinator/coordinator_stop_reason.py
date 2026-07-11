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

    CHECKPOINT_FAILED:
        Exploration state changed, but durable persistence failed.

        The coordinator stops immediately so in-memory exploration
        does not continue moving further ahead of the last durable
        checkpoint.

    RUNTIME_HEALTH_FAILED:
        A deterministic runtime-health check detected that the
        application under exploration is no longer healthy.

        Example:

            - application process disappeared
            - application window disappeared
            - unexpected error dialog appeared
            - application became unresponsive

        The detected failure is stored and checkpointed before the
        coordinator stops.
    """

    NO_REMAINING_TARGETS = "NO_REMAINING_TARGETS"

    MAX_STEPS_REACHED = "MAX_STEPS_REACHED"

    MAX_DURATION_REACHED = "MAX_DURATION_REACHED"

    MAX_FAILURES_REACHED = "MAX_FAILURES_REACHED"

    CHECKPOINT_FAILED = "CHECKPOINT_FAILED"

    RUNTIME_HEALTH_FAILED = "RUNTIME_HEALTH_FAILED"

    RECOVERY_FAILED = "RECOVERY_FAILED"