"""
File: recovery_executor.py

Purpose:
    Execute the mechanical steps required to recover an application.

Architecture:

RestartRecoveryPolicy
        │
        ▼
RecoveryExecutor
        │
        ├── Launch application
        ├── Connect window
        └── Return RecoveryExecutionResult

Important:

    RecoveryExecutor performs recovery mechanics only.

    It does NOT:

        - decide whether recovery should happen
        - replay application state
        - checkpoint
        - update the graph
        - update exploration memory
"""

import time

from agent.recovery.recovery_context import (
    RecoveryContext,
)

from agent.recovery.recovery_execution_result import (
    RecoveryExecutionResult,
)


class RecoveryExecutor:
    """
    Executes the mechanical recovery workflow.
    """

    def execute(
        self,
        context: RecoveryContext,
    ) -> RecoveryExecutionResult:

        start_time = time.time()

        try:

            context.ui_adapter.launch_application(
                context.executable
            )

            window = (
                context.ui_adapter.connect_window(
                    context.window_title
                )
            )

            return RecoveryExecutionResult(

                success=True,

                window=window,

                duration=(
                    time.time()
                    -
                    start_time
                ),
            )

        except Exception as error:

            return RecoveryExecutionResult(

                success=False,

                window=None,

                duration=(
                    time.time()
                    -
                    start_time
                ),

                error_message=str(
                    error
                ),
            )