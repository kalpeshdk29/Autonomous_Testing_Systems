"""
File: process_health_observation.py

Purpose:
    Represent one deterministic observation of the application
    process.

Architecture:

Operating System / Runtime Probe
        ↓
ProcessHealthObservation
        ↓
Application Failure Detector

Why This Component Exists:
    Failure detectors should classify facts.

    They should not directly query operating-system APIs.

    This separation gives us:

        - deterministic unit tests
        - reusable runtime probes
        - clear failure-classification boundaries
        - easier future support for non-Windows environments

Important:
    This object describes one observation only.

    It does not:

        - query the operating system
        - detect failures
        - create FailureRecord objects
        - recover the application
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProcessHealthObservation:
    """
    Immutable observation of one application process.

    Attributes
    ----------
    process_name:
        Expected application process name.

        Example:

            calc.exe

    process_id:
        Known operating-system process identifier.

        May be None when the process ID was never resolved.

    is_running:
        Whether the expected application process currently exists.

    source_state_id:
        Exploration state active when the observation was made.

    details:
        Optional human-readable probe information.
    """

    process_name: str

    process_id: int | None

    is_running: bool

    source_state_id: str

    details: str | None = None

    def __post_init__(
        self,
    ) -> None:
        """
        Validate observation data.
        """

        if (
            not isinstance(
                self.process_name,
                str,
            )
            or
            not self.process_name.strip()
        ):

            raise ValueError(
                "process_name must be a "
                "non-empty string."
            )

        if (
            self.process_id is not None
            and
            (
                not isinstance(
                    self.process_id,
                    int,
                )
                or
                self.process_id <= 0
            )
        ):

            raise ValueError(
                "process_id must be a positive "
                "integer or None."
            )

        if not isinstance(
            self.is_running,
            bool,
        ):

            raise ValueError(
                "is_running must be a boolean."
            )

        if (
            not isinstance(
                self.source_state_id,
                str,
            )
            or
            not self.source_state_id.strip()
        ):

            raise ValueError(
                "source_state_id must be a "
                "non-empty string."
            )

        if (
            self.details is not None
            and
            not isinstance(
                self.details,
                str,
            )
        ):

            raise ValueError(
                "details must be a string "
                "or None."
            )