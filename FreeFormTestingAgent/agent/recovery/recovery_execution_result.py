"""
File: recovery_execution_result.py

Purpose:
    Represent the mechanical outcome of one recovery execution.

Architecture:

RecoveryPolicy
        │
        ▼
RecoveryExecutor
        │
        ▼
RecoveryExecutionResult
        │
        ▼
RecoveryResult

Important:

    RecoveryExecutionResult describes what the executor
    accomplished mechanically.

    It does NOT decide whether recovery should be considered
    successful.

    That decision belongs to the RecoveryPolicy.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RecoveryExecutionResult:
    """
    Mechanical outcome produced by RecoveryExecutor.
    """

    success: bool

    window: Optional[object]

    duration: float

    error_message: Optional[str] = None

    def __post_init__(self):

        if not isinstance(
            self.success,
            bool,
        ):

            raise ValueError(
                "success must be a boolean."
            )

        if (
            not isinstance(
                self.duration,
                (int, float),
            )
            or
            self.duration < 0
        ):

            raise ValueError(
                "duration must be non-negative."
            )

        if (
            self.error_message is not None
            and
            (
                not isinstance(
                    self.error_message,
                    str,
                )
                or
                not self.error_message.strip()
            )
        ):

            raise ValueError(
                "error_message must be "
                "a non-empty string or None."
            )