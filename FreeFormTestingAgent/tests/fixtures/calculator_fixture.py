"""
Calculator test fixture.
"""

import subprocess
import time

from adapters.ui.windows_ui import (
    WindowsUIAdapter
)


def start_calculator():
    """
    Start a fresh calculator instance.
    """

    subprocess.Popen(
        ["calc.exe"]
    )

    time.sleep(1)

    ui = WindowsUIAdapter()

    window = ui.connect_window(
        "Calculator"
    )

    return ui, window


def stop_calculator():
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

def get_calculator():
    """
    Return a fresh calculator instance.
    """

    stop_calculator()

    return start_calculator()