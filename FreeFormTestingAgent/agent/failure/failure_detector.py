"""
File: failure_detector.py

Purpose:
    Define the common contract for deterministic failure detectors.

Architecture:

Runtime Observation
        ↓
FailureDetector
        ↓
FailureRecord | None

Why This Component Exists:
    Different failures are discovered from different signals.

    Examples:

        ExplorationStepResult
            → execution failure detector

        Process health
            → application disappeared detector

        Window health
            → window disappeared detector

        UI observation
            → unexpected error dialog detector

    All detectors should return the same stable FailureRecord
    domain object.

Important:
    A detector only answers:

        "Does this observation represent a failure?"

    It does not:

        - stop exploration
        - retry execution
        - recover the application
        - persist failures
        - decide severity
"""

from abc import ABC, abstractmethod

from agent.failure.failure_record import (
    FailureRecord,
)


class FailureDetector(ABC):
    """
    Base contract for deterministic failure detectors.
    """

    @abstractmethod
    def detect(
        self,
        observation,
    ) -> FailureRecord | None:
        """
        Inspect one observation.

        Returns
        -------
        FailureRecord:
            A deterministic failure was detected.

        None:
            This detector found no failure.
        """

        raise NotImplementedError