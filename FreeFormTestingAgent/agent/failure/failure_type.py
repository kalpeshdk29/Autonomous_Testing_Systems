"""
File: failure_type.py

Purpose:
    Define stable deterministic failure categories discovered
    during autonomous application exploration.

Architecture:

Application Runtime
        +
Replay
        +
Action Execution
        +
State Observation
        ↓
Failure Detection
        ↓
FailureType

Important:
    FailureType describes what failed.

    It does not contain:

        - failure evidence
        - state information
        - action information
        - recovery decisions

    Those belong to FailureRecord.
"""

from enum import Enum


class FailureType(Enum):
    """
    Stable category of a deterministic exploration failure.

    ACTION_EXECUTION_FAILED:
        The selected action could not be executed successfully.

    ACTION_TIMEOUT:
        Action execution exceeded its allowed time.

    REPLAY_FAILED:
        The framework could not replay the path required to reach
        the selected source state.

    REPLAY_STATE_MISMATCH:
        Replay completed but produced a state different from the
        state expected by the graph.

    APPLICATION_DISAPPEARED:
        The application process disappeared unexpectedly.

    WINDOW_DISAPPEARED:
        The expected application window disappeared while the
        application process may still exist.

    STATE_CAPTURE_FAILED:
        The framework could not observe and construct the current
        ApplicationState.

    UNEXPECTED_ERROR_DIALOG:
        An unexpected error dialog appeared during exploration.
    """

    ACTION_EXECUTION_FAILED = (
        "ACTION_EXECUTION_FAILED"
    )

    ACTION_TIMEOUT = (
        "ACTION_TIMEOUT"
    )

    REPLAY_FAILED = (
        "REPLAY_FAILED"
    )

    REPLAY_STATE_MISMATCH = (
        "REPLAY_STATE_MISMATCH"
    )

    APPLICATION_DISAPPEARED = (
        "APPLICATION_DISAPPEARED"
    )

    WINDOW_DISAPPEARED = (
        "WINDOW_DISAPPEARED"
    )

    STATE_CAPTURE_FAILED = (
        "STATE_CAPTURE_FAILED"
    )

    UNEXPECTED_ERROR_DIALOG = (
        "UNEXPECTED_ERROR_DIALOG"
    )