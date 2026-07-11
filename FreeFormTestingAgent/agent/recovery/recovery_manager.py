"""
RecoveryManager

Routes failures to the appropriate recovery policy.
"""

from agent.recovery.recovery_result import (
    RecoveryResult,
)


class RecoveryManager:

    def __init__(
        self,
        policy_registry,
    ):

        if policy_registry is None:

            raise ValueError(
                "policy_registry is required."
            )

        self._registry = dict(
            policy_registry
        )

    def recover(
        self,
        failure,
        context,
    ):

        policy = self._registry.get(
            failure.failure_type
        )

        if policy is None:

            return RecoveryResult(

                success=False,

                recovered_state_id=None,

                duration=0,

                failure_reason=(
                    "No recovery policy registered."
                ),
            )

        return policy.recover(

            failure,

            context,
        )