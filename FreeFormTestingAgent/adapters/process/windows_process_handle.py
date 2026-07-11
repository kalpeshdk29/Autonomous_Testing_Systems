"""
File: windows_process_handle.py

Purpose:
    Provide a process-like object for one exact Windows PID.

Architecture:

Known Windows PID
        ↓
WindowsProcessHandle
        ↓
ProcessHealthProbe
        ↓
ProcessHealthObservation

Compatibility:

    ProcessHealthProbe expects:

        process.pid
        process.poll()

    WindowsProcessHandle provides exactly that interface.

poll() semantics:

    None
        → tracked PID is still running

    integer
        → tracked PID has disappeared

Important:
    This component tracks one exact PID.

    It does not search globally by process name.
"""

import subprocess


class WindowsProcessHandle:
    """
    Process-like wrapper around one exact Windows process ID.
    """

    DISAPPEARED_RETURN_CODE = 1

    def __init__(
        self,
        process_id: int,
    ) -> None:

        if (
            not isinstance(
                process_id,
                int,
            )
            or
            process_id <= 0
        ):

            raise ValueError(
                "process_id must be a positive integer."
            )

        self.pid = process_id

    def poll(
        self,
    ) -> int | None:
        """
        Return current process state.

        Returns
        -------
        None:
            The exact tracked PID still exists.

        int:
            The exact tracked PID no longer exists.
        """

        result = subprocess.run(
            [
                "tasklist",
                "/FI",
                f"PID eq {self.pid}",
                "/FO",
                "CSV",
                "/NH",
            ],

            capture_output=True,

            text=True,

            check=False,
        )

        if result.returncode != 0:

            return (
                self.DISAPPEARED_RETURN_CODE
            )

        output = result.stdout.strip()

        if not output:

            return (
                self.DISAPPEARED_RETURN_CODE
            )

        if (
            "No tasks are running"
            in output
        ):

            return (
                self.DISAPPEARED_RETURN_CODE
            )

        expected_pid = (
            f'"{self.pid}"'
        )

        if expected_pid in output:

            return None

        return (
            self.DISAPPEARED_RETURN_CODE
        )