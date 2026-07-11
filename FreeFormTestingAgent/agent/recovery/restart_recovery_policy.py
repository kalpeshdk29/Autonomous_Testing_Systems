"""
File: restart_recovery_policy.py

Purpose:
    Recover from APPLICATION_DISAPPEARED by restarting the
    application.

Architecture:

FailureRecord
        │
        ▼
RestartRecoveryPolicy
        │
        ▼
RecoveryExecutor
        │
        ▼
RecoveryExecutionResult
        │
        ▼
RecoveryResult
"""

from agent.recovery.recovery_policy import (
    RecoveryPolicy,
)

from agent.recovery.recovery_result import (
    RecoveryResult,
)


class RestartRecoveryPolicy(
    RecoveryPolicy,
):
    """
    Recovery policy that delegates restart mechanics to the
    RecoveryExecutor.
    """

    def __init__(
        self,
        executor,
    ):

        if executor is None:

            raise ValueError("executor is required.")

        if not hasattr(
            executor,
            "execute",
        ):

            raise ValueError("executor must implement execute().")

        self._executor = executor

    def recover(
        self,
        failure,
        context,
    ):

        execution = self._executor.execute(context)

        return RecoveryResult(
            success=execution.success,
            recovered_state_id=(failure.source_state_id if execution.success else None),
            duration=execution.duration,
            failure_reason=(None if execution.success else execution.error_message),
        )
