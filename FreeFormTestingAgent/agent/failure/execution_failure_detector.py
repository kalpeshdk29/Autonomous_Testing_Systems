"""
File: execution_failure_detector.py

Purpose:
    Convert failed ExplorationStepResult outcomes into structured
    FailureRecord objects.

Architecture:

ExplorationStepResult
        ↓
ExecutionFailureDetector
        ↓
    ┌───────────────┐
    │               │
Failure         No Failure
    │               │
    ↓               ↓
FailureRecord       None

Current Supported Classifications:

    REPLAY_FAILED
        ↓
    FailureType.REPLAY_FAILED

    ACTION_EXECUTION_FAILED
        ↓
    FailureType.ACTION_EXECUTION_FAILED

Important:
    This detector intentionally handles only failures already
    represented by the current ExplorationStepResult contract.

    Other failure reasons such as:

        SOURCE_STATE_NOT_FOUND
        NO_ELIGIBLE_ACTION
        SOURCE_DEPTH_NOT_FOUND

    are currently framework/control-flow problems rather than
    application failures.

    They are not converted into FailureRecord objects here.
"""

from agent.explorer.exploration_step_result import (
    ExplorationStepResult,
)

from agent.failure.failure_detector import (
    FailureDetector,
)

from agent.failure.failure_record import (
    FailureRecord,
)

from agent.failure.failure_type import (
    FailureType,
)


class ExecutionFailureDetector(
    FailureDetector
):
    """
    Detect replay and action-execution failures from one
    ExplorationStepResult.
    """

    def detect(
        self,
        observation,
    ) -> FailureRecord | None:
        """
        Convert a supported failed step result into a FailureRecord.

        Unsupported framework/control-flow outcomes return None.
        """

        if not isinstance(
            observation,
            ExplorationStepResult,
        ):

            raise ValueError(
                "observation must be an "
                "ExplorationStepResult."
            )

        # =====================================================
        # REPLAY FAILURE
        # =====================================================

        if (
            observation.failure_reason
            ==
            "REPLAY_FAILED"
        ):

            return FailureRecord(
                failure_type=(
                    FailureType.REPLAY_FAILED
                ),

                message=(
                    "Replay could not restore "
                    "the selected source state."
                ),

                source_state_id=(
                    observation.source_state_id
                ),

                action=(
                    observation.selected_action
                ),

                target_state_id=(
                    observation.target_state_id
                ),

                recoverable=False,

                metadata={
                    "failure_reason": (
                        observation.failure_reason
                    ),

                    "replay_success": (
                        observation.replay_success
                    ),

                    "execution_success": (
                        observation.execution_success
                    ),

                    "duration": (
                        observation.duration
                    ),
                },
            )

        # =====================================================
        # ACTION EXECUTION FAILURE
        # =====================================================

        if (
            observation.failure_reason
            ==
            "ACTION_EXECUTION_FAILED"
        ):

            return FailureRecord(
                failure_type=(
                    FailureType
                    .ACTION_EXECUTION_FAILED
                ),

                message=(
                    "The selected action could "
                    "not be executed successfully."
                ),

                source_state_id=(
                    observation.source_state_id
                ),

                action=(
                    observation.selected_action
                ),

                target_state_id=(
                    observation.target_state_id
                ),

                recoverable=True,

                metadata={
                    "failure_reason": (
                        observation.failure_reason
                    ),

                    "replay_success": (
                        observation.replay_success
                    ),

                    "execution_success": (
                        observation.execution_success
                    ),

                    "duration": (
                        observation.duration
                    ),
                },
            )

        # =====================================================
        # NO SUPPORTED APPLICATION FAILURE
        # =====================================================

        return None