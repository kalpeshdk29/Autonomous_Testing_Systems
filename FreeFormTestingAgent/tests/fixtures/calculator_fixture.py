"""
File: calculator_fixture.py

Purpose:
    Provide a fresh calculator instance
    for integration tests.

Architecture:

Test
   ↓
CalculatorFixture
   ↓
Launch Calculator
   ↓
Return UI + Window
   ↓
Cleanup Calculator
"""

import subprocess
import time

from adapters.ui.windows_ui import (
    WindowsUIAdapter
)


class CalculatorFixture:
    """
    Calculator test fixture.

    Example
    -------

        with CalculatorFixture() as (
            ui,
            window
        ):
            ...
    """

    def __enter__(self):
        """
        Start fresh calculator.
        """

        self._kill_calculator()

        self.ui = WindowsUIAdapter()

        self.ui.launch_application(
            "calc.exe"
        )

        time.sleep(1)

        self.window = (
            self.ui.connect_window(
                "Calculator"
            )
        )

        return (
            self.ui,
            self.window
        )

    def __exit__(
        self,
        exc_type,
        exc_val,
        exc_tb
    ):
        """
        Cleanup calculator.
        """

        self._kill_calculator()

    def _kill_calculator(self):
        """
        Kill all calculator processes.
        """

        subprocess.run(
            [
                "taskkill",
                "/F",
                "/IM",
                "CalculatorApp.exe"
            ],
            capture_output=True
        )

        subprocess.run(
            [
                "taskkill",
                "/F",
                "/IM",
                "calc.exe"
            ],
            capture_output=True
        )