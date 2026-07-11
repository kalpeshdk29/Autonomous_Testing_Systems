"""
File:
    test_calculator_process_identity.py

Purpose:
    Determine which operating-system process identity should be
    tracked for Windows Calculator.

This is a diagnostic integration test.

It answers:

    1. What PID is returned by launching calc.exe?
    2. Does that process remain alive?
    3. What PID owns the connected Calculator window?
    4. Are the launcher PID and window PID the same?
"""

import subprocess
import time

from adapters.ui.windows_ui import (
    WindowsUIAdapter,
)


def kill_calculator():
    """
    Remove existing Calculator instances before and after the test.
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


def test_calculator_process_identity():
    """
    Inspect launcher and window process identities.
    """

    kill_calculator()

    try:

        ui = WindowsUIAdapter()

        # =====================================================
        # PHASE A
        # LAUNCH CALCULATOR
        # =====================================================

        print()

        print(
            "======================================"
        )

        print(
            "PHASE A: LAUNCH CALCULATOR"
        )

        print(
            "======================================"
        )

        process = ui.launch_application(
            "calc.exe"
        )

        print(
            "Launcher PID:",
            process.pid,
        )

        print(
            "Launcher poll() after launch:",
            process.poll(),
        )

        # =====================================================
        # PHASE B
        # CONNECT REAL WINDOW
        # =====================================================

        print()

        print(
            "======================================"
        )

        print(
            "PHASE B: CONNECT CALCULATOR WINDOW"
        )

        print(
            "======================================"
        )

        window = ui.connect_window(
            "Calculator"
        )

        print(
            "Window Name:",
            window.Name,
        )

        print(
            "Window Exists:",
            window.Exists(),
        )

        print(
            "Launcher poll() after window connect:",
            process.poll(),
        )

        # =====================================================
        # PHASE C
        # INSPECT WINDOW PROCESS ID
        # =====================================================

        print()

        print(
            "======================================"
        )

        print(
            "PHASE C: INSPECT PROCESS IDENTITY"
        )

        print(
            "======================================"
        )

        window_process_id = None

        try:

            window_process_id = (
                window.ProcessId
            )

        except Exception as error:

            print(
                "Could not read window.ProcessId:",
                repr(error),
            )

        print(
            "Launcher PID:",
            process.pid,
        )

        print(
            "Window Process ID:",
            window_process_id,
        )

        if window_process_id is not None:

            print(
                "Launcher PID Matches Window PID:",
                (
                    process.pid
                    ==
                    window_process_id
                ),
            )

        # =====================================================
        # PHASE D
        # WAIT AND RECHECK
        # =====================================================

        print()

        print(
            "======================================"
        )

        print(
            "PHASE D: WAIT AND RECHECK"
        )

        print(
            "======================================"
        )

        time.sleep(3)

        print(
            "Launcher poll() after wait:",
            process.poll(),
        )

        print(
            "Window Exists After Wait:",
            window.Exists(),
        )

        try:

            print(
                "Window Process ID After Wait:",
                window.ProcessId,
            )

        except Exception as error:

            print(
                "Could not re-read window ProcessId:",
                repr(error),
            )

        # =====================================================
        # MINIMUM DIAGNOSTIC ASSERTIONS
        # =====================================================

        assert process.pid > 0

        assert window.Exists()

        print()

        print(
            "======================================"
        )

        print(
            "CALCULATOR PROCESS IDENTITY DIAGNOSTIC COMPLETE"
        )

        print(
            "======================================"
        )

    finally:

        kill_calculator()


if __name__ == "__main__":

    test_calculator_process_identity()