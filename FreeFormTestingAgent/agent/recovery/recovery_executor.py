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
from agent.failure.failure_record import (
    FailureRecord,
)


class RecoveryExecutor:
    """
    Executes the mechanical recovery workflow.
    """

    def execute(
        self,
        failure: FailureRecord,
        context: RecoveryContext,
    ) -> RecoveryExecutionResult:

        start_time = time.time()

        try:

            window = (
                context.replay_engine.replay(

                    executable=context.executable,

                    window_title=context.window_title,

                    source_state=context.root_state_id,

                    target_state=failure.source_state_id,
                )
            )

            if window is None:

                return RecoveryExecutionResult(
                    success=False,
                    window=None,
                    duration=...,
                    error_message="Replay failed.",
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