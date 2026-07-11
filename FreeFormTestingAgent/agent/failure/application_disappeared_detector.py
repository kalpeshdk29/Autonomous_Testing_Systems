"""
File: application_disappeared_detector.py

Purpose:
    Detect when the expected application process has disappeared.

Architecture:

ProcessHealthObservation
        ↓
ApplicationDisappearedDetector
        ↓
    ┌───────────────┐
    │               │
Process Missing   Process Alive
    │               │
    ↓               ↓
FailureRecord       None

Classification:

    is_running == False
        ↓
    FailureType.APPLICATION_DISAPPEARED

Important:
    This detector classifies process-health facts.

    It does not:

        - query operating-system processes
        - kill or restart applications
        - inspect windows
        - decide whether exploration should stop
        - persist failures
"""

from agent.failure.failure_detector import (
    FailureDetector,
)

from agent.failure.failure_record import (
    FailureRecord,
)

from agent.failure.failure_type import (
    FailureType,
)

from agent.failure.process_health_observation import (
    ProcessHealthObservation,
)


class ApplicationDisappearedDetector(
    FailureDetector
):
    """
    Detect disappearance of the expected application process.
    """

    def detect(
        self,
        observation,
    ) -> FailureRecord | None:
        """
        Convert a missing-process observation into a structured
        FailureRecord.

        Returns
        -------
        FailureRecord:
            The expected process is no longer running.

        None:
            The expected process is still running.
        """

        if not isinstance(
            observation,
            ProcessHealthObservation,
        ):

            raise ValueError(
                "observation must be a "
                "ProcessHealthObservation."
            )

        if observation.is_running:

            return None

        return FailureRecord(
            failure_type=(
                FailureType
                .APPLICATION_DISAPPEARED
            ),

            message=(
                "The expected application process "
                "disappeared unexpectedly."
            ),

            source_state_id=(
                observation.source_state_id
            ),

            action=None,

            target_state_id=None,

            replay_path=[],

            screenshot_path=None,

            recoverable=True,

            metadata={
                "process_name": (
                    observation.process_name
                ),

                "process_id": (
                    observation.process_id
                ),

                "is_running": (
                    observation.is_running
                ),

                "details": (
                    observation.details
                ),
            },
        )