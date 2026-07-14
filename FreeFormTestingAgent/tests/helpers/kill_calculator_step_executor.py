"""
File:
    kill_calculator_step_executor.py

Purpose:
    Inject a deterministic Calculator crash during a real
    coordinator run.

Architecture:

Coordinator
      ↓
KillCalculatorStepExecutor
      ↓
Real ExplorationStepExecutor
      ↓
Real Calculator

After N successful exploration steps:

      ↓
taskkill Calculator

The coordinator is completely unaware that the crash was
injected. RuntimeHealthMonitor must discover it naturally.
"""

import subprocess


class KillCalculatorStepExecutor:
    """
    Decorates the real exploration step executor.

    After a configurable number of successful steps the
    Calculator process is terminated.
    """

    def __init__(
        self,
        step_executor,
        kill_after_steps=1,
    ):

        self._executor = step_executor

        self._kill_after_steps = kill_after_steps

        self._successful_steps = 0

        self._killed = False

    def execute_step(
        self,
        root_state_id,
        source_state_id,
    ):

        result = self._executor.execute_step(
            root_state_id,
            source_state_id,
        )

        if (
            result.execution_success
            and
            not self._killed
        ):

            self._successful_steps += 1

            if (
                self._successful_steps
                >= self._kill_after_steps
            ):

                print()

                print(
                    "======================================"
                )

                print(
                    "FAULT INJECTION"
                )

                print(
                    "======================================"
                )

                print(
                    "Terminating Calculator..."
                )

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

                print(
                    "Calculator terminated."
                )

                self._killed = True

        return result