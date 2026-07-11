"""
File:
    test_calculator_application_disappeared.py

Purpose:
    Verify real operating-system detection of Calculator process
    disappearance.

Complete Flow:

    Launch real Calculator
        ↓
    Connect real Calculator window
        ↓
    Capture window-owning PID
        ↓
    WindowsProcessHandle
        ↓
    ProcessHealthProbe
        ↓
    Healthy observation
        ↓
    Kill exact tracked PID
        ↓
    ProcessHealthProbe
        ↓
    Missing-process observation
        ↓
    ApplicationDisappearedDetector
        ↓
    FailureRecord(
        APPLICATION_DISAPPEARED
    )

Important:
    This test tracks the PID that owns the real Calculator window.

    It does not track the calc.exe launcher because the launcher
    exits immediately after starting the real Calculator process.
"""

import subprocess
import time


from adapters.process.windows_process_handle import (
    WindowsProcessHandle,
)

from adapters.ui.windows_ui import (
    WindowsUIAdapter,
)


from agent.failure.application_disappeared_detector import (
    ApplicationDisappearedDetector,
)

from agent.failure.failure_type import (
    FailureType,
)

from agent.failure.process_health_probe import (
    ProcessHealthProbe,
)


# =============================================================
# CONFIGURATION
# =============================================================


WINDOW_NAME = "Calculator"

PROCESS_NAME = "CalculatorApp.exe"

SOURCE_STATE_ID = (
    "calculator-process-health-integration-state"
)


# =============================================================
# HELPERS
# =============================================================


def kill_all_calculator_processes():
    """
    Remove Calculator instances before and after the test.

    This is cleanup only.

    The actual failure injection kills one exact tracked PID.
    """

    subprocess.run(
        [
            "taskkill",
            "/F",
            "/IM",
            "CalculatorApp.exe",
        ],

        capture_output=True,
    )

    subprocess.run(
        [
            "taskkill",
            "/F",
            "/IM",
            "calc.exe",
        ],

        capture_output=True,
    )


def kill_exact_process(
    process_id: int,
):
    """
    Kill only the exact application process being tracked.
    """

    result = subprocess.run(
        [
            "taskkill",
            "/F",
            "/PID",
            str(process_id),
        ],

        capture_output=True,

        text=True,
    )

    if result.returncode != 0:

        raise RuntimeError(
            "Failed to terminate tracked "
            f"Calculator PID {process_id}. "
            f"stdout={result.stdout!r}, "
            f"stderr={result.stderr!r}"
        )


def wait_for_process_disappearance(
    probe: ProcessHealthProbe,
    source_state_id: str,
    timeout: float = 10.0,
):
    """
    Poll until the tracked process disappears.

    Process termination is asynchronous, so the test must not
    assume the process vanishes immediately after taskkill.
    """

    deadline = (
        time.time()
        +
        timeout
    )

    latest_observation = None

    while time.time() < deadline:

        latest_observation = (
            probe.observe(
                source_state_id=(
                    source_state_id
                )
            )
        )

        if not latest_observation.is_running:

            return latest_observation

        time.sleep(0.2)

    raise AssertionError(
        "Tracked Calculator process did not "
        f"disappear within {timeout} seconds. "
        f"Latest observation: {latest_observation}"
    )


# =============================================================
# REAL INTEGRATION TEST
# =============================================================


def test_calculator_application_disappeared():
    """
    Verify real Calculator process disappearance detection.
    """

    kill_all_calculator_processes()

    try:

        # =====================================================
        # PHASE A
        # LAUNCH REAL CALCULATOR
        # =====================================================

        print()

        print(
            "======================================"
        )

        print(
            "PHASE A: LAUNCH REAL CALCULATOR"
        )

        print(
            "======================================"
        )

        ui = WindowsUIAdapter()

        launcher_process = (
            ui.launch_application(
                "calc.exe"
            )
        )

        window = ui.connect_window(
            WINDOW_NAME
        )

        tracked_process_id = (
            window.ProcessId
        )

        print(
            "Launcher PID:",
            launcher_process.pid,
        )

        print(
            "Launcher Exit Code:",
            launcher_process.poll(),
        )

        print(
            "Tracked Window PID:",
            tracked_process_id,
        )

        assert (
            tracked_process_id
            >
            0
        )

        # =====================================================
        # PHASE B
        # BUILD REAL PROCESS HEALTH PIPELINE
        # =====================================================

        print()

        print(
            "======================================"
        )

        print(
            "PHASE B: BUILD PROCESS HEALTH PIPELINE"
        )

        print(
            "======================================"
        )

        process_handle = (
            WindowsProcessHandle(
                process_id=(
                    tracked_process_id
                )
            )
        )

        probe = ProcessHealthProbe(
            process_name=(
                PROCESS_NAME
            ),

            process=(
                process_handle
            ),
        )

        detector = (
            ApplicationDisappearedDetector()
        )

        print(
            "Tracked PID:",
            process_handle.pid,
        )

        # =====================================================
        # PHASE C
        # VERIFY HEALTHY APPLICATION
        # =====================================================

        print()

        print(
            "======================================"
        )

        print(
            "PHASE C: VERIFY HEALTHY APPLICATION"
        )

        print(
            "======================================"
        )

        healthy_observation = (
            probe.observe(
                source_state_id=(
                    SOURCE_STATE_ID
                )
            )
        )

        print(
            "Process Name:",
            healthy_observation
            .process_name,
        )

        print(
            "Process ID:",
            healthy_observation
            .process_id,
        )

        print(
            "Is Running:",
            healthy_observation
            .is_running,
        )

        print(
            "Details:",
            healthy_observation
            .details,
        )

        assert (
            healthy_observation.is_running
        )

        assert (
            healthy_observation.process_id
            ==
            tracked_process_id
        )

        healthy_failure = (
            detector.detect(
                healthy_observation
            )
        )

        assert (
            healthy_failure
            is None
        )

        # =====================================================
        # PHASE D
        # KILL EXACT TRACKED APPLICATION PID
        # =====================================================

        print()

        print(
            "======================================"
        )

        print(
            "PHASE D: KILL EXACT TRACKED PID"
        )

        print(
            "======================================"
        )

        print(
            "Killing PID:",
            tracked_process_id,
        )

        kill_exact_process(
            tracked_process_id
        )

        # =====================================================
        # PHASE E
        # OBSERVE REAL PROCESS DISAPPEARANCE
        # =====================================================

        print()

        print(
            "======================================"
        )

        print(
            "PHASE E: OBSERVE DISAPPEARANCE"
        )

        print(
            "======================================"
        )

        missing_observation = (
            wait_for_process_disappearance(
                probe=probe,

                source_state_id=(
                    SOURCE_STATE_ID
                ),
            )
        )

        print(
            "Process Name:",
            missing_observation
            .process_name,
        )

        print(
            "Process ID:",
            missing_observation
            .process_id,
        )

        print(
            "Is Running:",
            missing_observation
            .is_running,
        )

        print(
            "Details:",
            missing_observation
            .details,
        )

        assert (
            missing_observation.is_running
            is False
        )

        assert (
            missing_observation.process_id
            ==
            tracked_process_id
        )

        # =====================================================
        # PHASE F
        # DETECT STRUCTURED APPLICATION FAILURE
        # =====================================================

        print()

        print(
            "======================================"
        )

        print(
            "PHASE F: DETECT APPLICATION FAILURE"
        )

        print(
            "======================================"
        )

        failure = detector.detect(
            missing_observation
        )

        assert failure is not None

        assert (
            failure.failure_type
            ==
            FailureType
            .APPLICATION_DISAPPEARED
        )

        assert (
            failure.source_state_id
            ==
            SOURCE_STATE_ID
        )

        assert (
            failure.metadata[
                "process_name"
            ]
            ==
            PROCESS_NAME
        )

        assert (
            failure.metadata[
                "process_id"
            ]
            ==
            tracked_process_id
        )

        assert (
            failure.metadata[
                "is_running"
            ]
            is False
        )

        assert failure.recoverable

        print(
            "Failure ID:",
            failure.failure_id,
        )

        print(
            "Failure Type:",
            failure.failure_type,
        )

        print(
            "Source State:",
            failure.source_state_id,
        )

        print(
            "Recoverable:",
            failure.recoverable,
        )

        print(
            "Metadata:",
            failure.metadata,
        )

        # =====================================================
        # FINAL RESULT
        # =====================================================

        print()

        print(
            "======================================"
        )

        print(
            "REAL APPLICATION DISAPPEARANCE VERIFIED"
        )

        print(
            "======================================"
        )

        print(
            "Launcher PID:",
            launcher_process.pid,
        )

        print(
            "Tracked Application PID:",
            tracked_process_id,
        )

        print(
            "Healthy Before Kill:",
            healthy_observation.is_running,
        )

        print(
            "Missing After Kill:",
            (
                not
                missing_observation.is_running
            ),
        )

        print(
            "Failure Type:",
            failure.failure_type,
        )

        print(
            "Process ID Preserved:",
            (
                failure.metadata[
                    "process_id"
                ]
                ==
                tracked_process_id
            ),
        )

        print()

        print(
            "CALCULATOR APPLICATION DISAPPEARED "
            "TEST PASSED"
        )

    finally:

        kill_all_calculator_processes()


if __name__ == "__main__":

    test_calculator_application_disappeared()