"""
Failure detection domain package.

This package contains the stable domain models used to represent
deterministic failures discovered during autonomous exploration.
"""

from agent.failure.failure_type import (
    FailureType,
)

from agent.failure.failure_record import (
    FailureRecord,
)


__all__ = [
    "FailureType",
    "FailureRecord",
]