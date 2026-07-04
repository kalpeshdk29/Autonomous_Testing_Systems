"""
File: exploration_limits.py

Purpose:
    Defines safety boundaries for an exploration session.

Architecture:

Explorer Statistics
        ↓
ExplorationLimits
        ↓
Check Current Progress
        ↓
Continue / Stop

Why This Component Exists:
    Autonomous exploration must never run without boundaries.

    Without limits, an explorer could:

        - discover too many states,
        - execute too many actions,
        - create too many transitions,
        - run for too long,
        - repeatedly encounter failures.

    This class stores the configured boundaries.

Important:
    This class only stores configuration.

    The explorer is responsible for checking these limits
    during execution.
"""

from dataclasses import dataclass


@dataclass
class ExplorationLimits:
    """
    Configuration for exploration safety limits.

    Parameters
    ----------
    max_states:
        Maximum number of unique states that may exist
        during one exploration session.

    max_actions:
        Maximum number of actions that may be attempted.

    max_transitions:
        Maximum number of transitions that may be stored.

    max_duration:
        Maximum exploration duration in seconds.

    max_failures:
        Maximum number of failed action executions.

    Notes
    -----
    A value of None means that the specific limit
    is disabled.

    Example
    -------

        ExplorationLimits(
            max_states=100,
            max_actions=500,
            max_transitions=500,
            max_duration=120.0,
            max_failures=20
        )
    """

    max_states: int | None = 100

    max_actions: int | None = 500

    max_transitions: int | None = 500

    max_depth: int | None = 10

    max_duration: float | None = 300.0

    max_failures: int | None = 20