"""
File: failure_store.py

Purpose:
    Store structured failures discovered during one autonomous
    runtime.

Architecture:

FailureDetector
        ↓
FailureRecord
        ↓
FailureStore

Why This Component Exists:
    Failure detection and failure storage are separate concerns.

    A detector answers:

        "Did this observation represent a failure?"

    The store answers:

        "Which structured failures have been discovered?"

Important:
    This is currently an in-memory runtime store.

    Durable session persistence will be added later after the
    coordinator integration is proven.
"""

from agent.failure.failure_record import (
    FailureRecord,
)


class FailureStore:
    """
    Ordered in-memory collection of FailureRecord objects.
    """

    def __init__(
        self,
    ):
        self._failures: list[
            FailureRecord
        ] = []

    def add(
        self,
        failure: FailureRecord,
    ) -> None:
        """
        Store one structured failure.
        """

        if not isinstance(
            failure,
            FailureRecord,
        ):

            raise ValueError(
                "failure must be a "
                "FailureRecord."
            )

        self._failures.append(
            failure
        )

    @property
    def failures(
        self,
    ) -> list[FailureRecord]:
        """
        Return a copy of the ordered failure history.

        Returning a copy prevents callers from mutating the
        internal list directly.
        """

        return list(
            self._failures
        )

    @property
    def count(
        self,
    ) -> int:
        """
        Return the number of stored failures.
        """

        return len(
            self._failures
        )

    def clear(
        self,
    ) -> None:
        """
        Remove all stored failures.
        """

        self._failures.clear()