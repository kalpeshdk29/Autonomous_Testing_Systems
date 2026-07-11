"""
File: recovery_result.py

Purpose:
    Represent the outcome of one recovery attempt.

Architecture:

FailureRecord
        ↓
RecoveryPolicy
        ↓
RecoveryResult

A RecoveryResult answers one question:

    "Did recovery succeed, and what happened?"

It does not:

    - decide recovery policy
    - restart applications
    - replay paths
    - modify the exploration graph
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RecoveryResult:
    """
    Result of one recovery attempt.
    """

    success: bool

    recovered_state_id: Optional[str]

    duration: float

    failure_reason: Optional[str] = None

    def __post_init__(self):

        if not isinstance(self.success, bool):

            raise ValueError(
                "success must be a boolean."
            )

        if (
            self.recovered_state_id is not None
            and
            (
                not isinstance(
                    self.recovered_state_id,
                    str,
                )
                or
                not self.recovered_state_id.strip()
            )
        ):

            raise ValueError(
                "recovered_state_id must be "
                "a non-empty string or None."
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
            self.failure_reason is not None
            and
            (
                not isinstance(
                    self.failure_reason,
                    str,
                )
                or
                not self.failure_reason.strip()
            )
        ):

            raise ValueError(
                "failure_reason must be "
                "a non-empty string or None."
            )