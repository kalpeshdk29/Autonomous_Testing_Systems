"""
File: runtime_health_monitor.py

Purpose:
    Coordinate runtime-health observation and failure detection.

Architecture:

Runtime Probe
        ↓
RuntimeHealthMonitor
        ↓
Observation
        ↓
Failure Detector
        ↓
FailureRecord | None

Initial Runtime:

    ProcessHealthProbe
        +
    ApplicationDisappearedDetector

Future Runtime:

    RuntimeHealthMonitor
        ├── process health
        ├── window health
        ├── error dialogs
        └── application responsiveness

Important:
    This component does not:

        - store failures
        - checkpoint sessions
        - stop exploration
        - recover applications

    Those decisions belong to the coordinator and future recovery
    policies.
"""


class RuntimeHealthMonitor:
    """
    Execute one runtime-health observation and classification.
    """

    def __init__(
        self,
        probe,
        detector,
    ) -> None:

        if probe is None:

            raise ValueError(
                "probe is required."
            )

        if not callable(
            getattr(
                probe,
                "observe",
                None,
            )
        ):

            raise ValueError(
                "probe must provide observe()."
            )

        if detector is None:

            raise ValueError(
                "detector is required."
            )

        if not callable(
            getattr(
                detector,
                "detect",
                None,
            )
        ):

            raise ValueError(
                "detector must provide detect()."
            )

        self.probe = probe

        self.detector = detector

    def check(
        self,
        source_state_id: str,
    ):
        """
        Observe current runtime health and classify the result.

        Returns
        -------
        FailureRecord:
            Runtime failure detected.

        None:
            Runtime is healthy.
        """

        if (
            not isinstance(
                source_state_id,
                str,
            )
            or
            not source_state_id.strip()
        ):

            raise ValueError(
                "source_state_id must be a "
                "non-empty string."
            )

        observation = (
            self.probe.observe(
                source_state_id=(
                    source_state_id
                )
            )
        )

        return self.detector.detect(
            observation
        )