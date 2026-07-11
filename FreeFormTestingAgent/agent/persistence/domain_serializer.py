"""
File: domain_serializer.py

Purpose:
    Convert runtime domain objects to JSON-compatible dictionaries
    and reconstruct the original runtime objects.

Architecture:

Runtime Domain Object
        ↓
Serializable Dictionary
        ↓
JSON

JSON Dictionary
        ↓
Domain Reconstruction
        ↓
Runtime Domain Object

Supported Objects:

    - Action
    - ApplicationState
    - Transition
    - ExplorationMemory
    - FailureRecord

Important:
    This component does not read or write files.
"""

from datetime import datetime

from core.models.action import Action
from core.models.state import ApplicationState
from core.models.transition import Transition

from agent.failure.failure_record import (
    FailureRecord,
)

from agent.failure.failure_type import (
    FailureType,
)

from agent.memory.exploration_memory import (
    ExplorationMemory,
)


class DomainSerializer:
    """
    Serialize and deserialize exploration domain objects.
    """

    # =========================================================
    # ACTION
    # =========================================================

    @staticmethod
    def serialize_action(
        action: Action,
    ) -> dict:

        return action.model_dump(
            mode="json"
        )

    @staticmethod
    def deserialize_action(
        data: dict,
    ) -> Action:

        return Action.model_validate(
            data
        )

    # =========================================================
    # APPLICATION STATE
    # =========================================================

    @staticmethod
    def serialize_state(
        state: ApplicationState,
    ) -> dict:

        return state.model_dump(
            mode="json"
        )

    @staticmethod
    def deserialize_state(
        data: dict,
    ) -> ApplicationState:

        return ApplicationState.model_validate(
            data
        )

    # =========================================================
    # TRANSITION
    # =========================================================

    @staticmethod
    def serialize_transition(
        transition: Transition,
    ) -> dict:

        return {
            "source_state": (
                transition.source_state
            ),

            "target_state": (
                transition.target_state
            ),

            "action": (
                DomainSerializer
                .serialize_action(
                    transition.action
                )
            ),

            "success": (
                transition.success
            ),

            "duration": (
                transition.duration
            ),
        }

    @staticmethod
    def deserialize_transition(
        data: dict,
    ) -> Transition:

        return Transition(
            source_state=data[
                "source_state"
            ],

            target_state=data[
                "target_state"
            ],

            action=(
                DomainSerializer
                .deserialize_action(
                    data["action"]
                )
            ),

            success=data.get(
                "success",
                True,
            ),

            duration=data.get(
                "duration",
                0.0,
            ),
        )

    # =========================================================
    # EXPLORATION MEMORY
    # =========================================================

    @staticmethod
    def serialize_memory(
        memory: ExplorationMemory,
    ) -> dict:

        return {
            "visited_actions": {
                state_hash: sorted(
                    action_targets
                )

                for (
                    state_hash,
                    action_targets,
                )

                in memory
                .visited_actions
                .items()
            }
        }

    @staticmethod
    def deserialize_memory(
        data: dict,
    ) -> ExplorationMemory:

        memory = ExplorationMemory()

        visited_actions = data.get(
            "visited_actions",
            {},
        )

        for (
            state_hash,
            action_targets,
        ) in visited_actions.items():

            for action_target in action_targets:

                memory.mark_executed(
                    state_hash,
                    action_target,
                )

        return memory

    # =========================================================
    # FAILURE RECORD
    # =========================================================

    @staticmethod
    def serialize_failure(
        failure: FailureRecord,
    ) -> dict:
        """
        Convert one FailureRecord into JSON-compatible data.

        Nested replay transitions and actions are serialized
        explicitly.
        """

        if not isinstance(
            failure,
            FailureRecord,
        ):

            raise ValueError(
                "failure must be a "
                "FailureRecord."
            )

        return {
            "failure_id": (
                failure.failure_id
            ),

            "failure_type": (
                failure.failure_type.value
            ),

            "message": (
                failure.message
            ),

            "timestamp": (
                failure.timestamp.isoformat()
            ),

            "source_state_id": (
                failure.source_state_id
            ),

            "action": (
                DomainSerializer
                .serialize_action(
                    failure.action
                )
                if failure.action
                is not None
                else None
            ),

            "target_state_id": (
                failure.target_state_id
            ),

            "replay_path": [
                DomainSerializer
                .serialize_transition(
                    transition
                )

                for transition
                in failure.replay_path
            ],

            "screenshot_path": (
                failure.screenshot_path
            ),

            "recoverable": (
                failure.recoverable
            ),

            "metadata": (
                failure.metadata
            ),
        }

    @staticmethod
    def deserialize_failure(
        data: dict,
    ) -> FailureRecord:
        """
        Reconstruct one FailureRecord.

        Restores:

            string
                → FailureType

            ISO timestamp
                → datetime

            action dictionary
                → Action

            replay-path dictionaries
                → Transition objects
        """

        if not isinstance(
            data,
            dict,
        ):

            raise ValueError(
                "Serialized failure must "
                "be a dictionary."
            )

        failure_type_value = data.get(
            "failure_type"
        )

        try:

            failure_type = FailureType(
                failure_type_value
            )

        except (
            ValueError,
            TypeError,
        ) as error:

            raise ValueError(
                "Unsupported failure type: "
                f"{failure_type_value}."
            ) from error

        timestamp_value = data.get(
            "timestamp"
        )

        if not timestamp_value:

            raise ValueError(
                "Serialized failure timestamp "
                "is missing."
            )

        action_data = data.get(
            "action"
        )

        return FailureRecord(
            failure_id=data.get(
                "failure_id"
            ),

            failure_type=(
                failure_type
            ),

            message=data.get(
                "message"
            ),

            timestamp=(
                datetime.fromisoformat(
                    timestamp_value
                )
            ),

            source_state_id=data.get(
                "source_state_id"
            ),

            action=(
                DomainSerializer
                .deserialize_action(
                    action_data
                )
                if action_data
                is not None
                else None
            ),

            target_state_id=data.get(
                "target_state_id"
            ),

            replay_path=[
                DomainSerializer
                .deserialize_transition(
                    transition_data
                )

                for transition_data
                in data.get(
                    "replay_path",
                    [],
                )
            ],

            screenshot_path=data.get(
                "screenshot_path"
            ),

            recoverable=data.get(
                "recoverable",
                False,
            ),

            metadata=data.get(
                "metadata",
                {},
            ),
        )