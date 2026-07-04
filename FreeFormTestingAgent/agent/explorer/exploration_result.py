"""
File: exploration_result.py

Purpose:
    Stores the final result and statistics
    of an exploration session.

Architecture:

Explorer
    ↓
Exploration Statistics
    ↓
ExplorationResult
"""

from dataclasses import dataclass

from agent.explorer.exploration_stop_reason import (
    ExplorationStopReason
)


@dataclass
class ExplorationResult:
    """
    Final result of an exploration session.

    Attributes
    ----------
    states:
        Number of unique states discovered.

    transitions:
        Number of transitions created.

    actions:
        Number of actions attempted.

    failures:
        Number of failed action executions.

    duration:
        Total exploration duration in seconds.

    stop_reason:
        Reason why exploration ended.
    """

    states: int

    transitions: int

    actions: int

    failures: int

    duration: float

    stop_reason: ExplorationStopReason