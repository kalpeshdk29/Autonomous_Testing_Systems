"""
File: process_health_probe.py

Purpose:
    Observe the current health of one known operating-system
    process.

Architecture:

Known Process Handle
        ↓
ProcessHealthProbe
        ↓
ProcessHealthObservation
        ↓
ApplicationDisappearedDetector

Important:
    This component observes process state.

    It does not:

        - classify failures
        - create FailureRecord objects
        - restart applications
        - persist failures

Design:
    The probe accepts a process-like object instead of depending
    directly on subprocess.Popen.

    The object must provide:

        - pid
        - poll()

    This keeps the probe deterministic and easy to unit-test.
"""

from agent.failure.process_health_observation import (
    ProcessHealthObservation,
)


class ProcessHealthProbe:
    """
    Observe one known application process.
    """

    def __init__(
        self,
        process_name: str,
        process,
    ) -> None:

        if (
            not isinstance(
                process_name,
                str,
            )
            or not process_name.strip()
        ):

            raise ValueError("process_name must be a " "non-empty string.")

        if process is None:

            raise ValueError("process is required.")

        if not hasattr(
            process,
            "pid",
        ):

            raise ValueError("process must provide a pid.")

        if not callable(
            getattr(
                process,
                "poll",
                None,
            )
        ):

            raise ValueError("process must provide poll().")

        process_id = process.pid

        if (
            not isinstance(
                process_id,
                int,
            )
            or process_id <= 0
        ):

            raise ValueError("process.pid must be a " "positive integer.")

        self.process_name = process_name

        self.process = process

    def observe(
        self,
        source_state_id: str,
    ) -> ProcessHealthObservation:
        """
        Observe whether the tracked process is still running.

        subprocess.Popen.poll():

            None
                → process is still running

            integer exit code
                → process has terminated
        """

        return_code = self.process.poll()

        is_running = return_code is None

        if is_running:

            details = "Tracked process is running."

        else:

            details = "Tracked process terminated " f"with exit code {return_code}."

        return ProcessHealthObservation(
            process_name=(self.process_name),
            process_id=(self.process.pid),
            is_running=(is_running),
            source_state_id=(source_state_id),
            details=details,
        )
