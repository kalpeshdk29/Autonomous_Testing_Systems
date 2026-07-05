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

Important:
    This component does not read or write files.

    Filesystem persistence belongs to the future
    JsonSessionRepository.
"""

from core.models.action import Action
from core.models.state import ApplicationState
from core.models.transition import Transition

from agent.memory.exploration_memory import (
    ExplorationMemory,
)


class DomainSerializer:
    """
    Serialize and deserialize core exploration domain objects.

    Supported objects:

        - Action
        - ApplicationState
        - Transition
        - ExplorationMemory

    The serializer returns only JSON-compatible structures.
    """

    # =========================================================
    # ACTION
    # =========================================================

    @staticmethod
    def serialize_action(
        action: Action,
    ) -> dict:
        """
        Convert an Action into a JSON-compatible dictionary.

        Pydantic JSON mode converts:

            ActionType → string value
            datetime   → ISO-8601 string
        """

        return action.model_dump(
            mode="json"
        )

    @staticmethod
    def deserialize_action(
        data: dict,
    ) -> Action:
        """
        Reconstruct an Action from serialized data.

        Pydantic restores:

            string → ActionType
            ISO string → datetime
        """

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
        """
        Convert an ApplicationState into a JSON-compatible
        dictionary.

        Nested UIControl and Action objects are serialized by
        Pydantic.
        """

        return state.model_dump(
            mode="json"
        )

    @staticmethod
    def deserialize_state(
        data: dict,
    ) -> ApplicationState:
        """
        Reconstruct an ApplicationState including nested controls
        and available actions.
        """

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
        """
        Convert a Transition into a JSON-compatible dictionary.

        Transition is a dataclass, so its nested Action is
        serialized explicitly.
        """

        return {
            "source_state": (
                transition.source_state
            ),

            "target_state": (
                transition.target_state
            ),

            "action": (
                DomainSerializer.serialize_action(
                    transition.action
                )
            ),

            "success": transition.success,

            "duration": transition.duration,
        }

    @staticmethod
    def deserialize_transition(
        data: dict,
    ) -> Transition:
        """
        Reconstruct a Transition with a real Action object.
        """

        return Transition(
            source_state=data[
                "source_state"
            ],

            target_state=data[
                "target_state"
            ],

            action=(
                DomainSerializer.deserialize_action(
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
        """
        Convert ExplorationMemory into JSON-compatible data.

        Runtime:

            defaultdict(set)

        Serialized:

            dict[str, list[str]]

        Targets are sorted so saved output is deterministic.
        """

        return {
            "visited_actions": {
                state_hash: sorted(
                    action_targets
                )

                for (
                    state_hash,
                    action_targets,
                )

                in memory.visited_actions.items()
            }
        }

    @staticmethod
    def deserialize_memory(
        data: dict,
    ) -> ExplorationMemory:
        """
        Reconstruct ExplorationMemory through its public API.

        We deliberately do not replace visited_actions directly.

        Using mark_executed() preserves the runtime structure and
        keeps reconstruction independent from internal storage.
        """

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