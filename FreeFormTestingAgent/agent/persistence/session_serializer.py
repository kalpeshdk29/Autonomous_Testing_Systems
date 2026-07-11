"""
File: session_serializer.py

Purpose:
    Serialize and deserialize complete exploration sessions.

Architecture:

ExplorationSessionSnapshot
        ↓
SessionSerializer
        ↓
JSON-Compatible Dictionary

JSON-Compatible Dictionary
        ↓
Schema Validation
        ↓
Graph Reconstruction
        ↓
Memory Reconstruction
        ↓
Failure Reconstruction
        ↓
ExplorationSessionSnapshot

Important:
    This component does not perform file I/O.
"""

from datetime import datetime

from agent.persistence.domain_serializer import (
    DomainSerializer,
)

from agent.persistence.session_snapshot import (
    ExplorationSessionSnapshot,
)

from agent.persistence.state_graph_serializer import (
    StateGraphSerializer,
)

from agent.persistence.session_status import (
    SessionStatus,
)


class SessionSerializer:
    """
    Serialize and deserialize complete exploration sessions.
    """

    CURRENT_SCHEMA_VERSION = 1

    # =========================================================
    # SERIALIZATION
    # =========================================================

    @classmethod
    def serialize(
        cls,
        snapshot: ExplorationSessionSnapshot,
    ) -> dict:

        cls._validate_schema_version(
            snapshot.schema_version
        )

        cls._validate_root_state(
            root_state_id=(
                snapshot.root_state_id
            ),

            graph=snapshot.graph,
        )

        return {
            "schema_version": (
                snapshot.schema_version
            ),

            "session": {
                "session_id": (
                    snapshot.session_id
                ),

                "root_state_id": (
                    snapshot.root_state_id
                ),

                "status": (
                    snapshot.status.value
                ),

                "created_at": (
                    snapshot
                    .created_at
                    .isoformat()
                ),

                "updated_at": (
                    snapshot
                    .updated_at
                    .isoformat()
                ),
            },

            "graph": (
                StateGraphSerializer
                .serialize(
                    snapshot.graph
                )
            ),

            "memory": (
                DomainSerializer
                .serialize_memory(
                    snapshot.memory
                )
            ),

            "failures": [
                DomainSerializer
                .serialize_failure(
                    failure
                )

                for failure
                in snapshot.failures
            ],
        }

    # =========================================================
    # DESERIALIZATION
    # =========================================================

    @classmethod
    def deserialize(
        cls,
        data: dict,
    ) -> ExplorationSessionSnapshot:

        schema_version = data.get(
            "schema_version"
        )

        cls._validate_schema_version(
            schema_version
        )

        session_data = data.get(
            "session"
        )

        if not isinstance(
            session_data,
            dict,
        ):

            raise ValueError(
                "Serialized session metadata "
                "is missing."
            )

        session_id = session_data.get(
            "session_id"
        )

        root_state_id = session_data.get(
            "root_state_id"
        )

        status_value = session_data.get(
            "status"
        )

        created_at_value = (
            session_data.get(
                "created_at"
            )
        )

        updated_at_value = (
            session_data.get(
                "updated_at"
            )
        )

        if not session_id:

            raise ValueError(
                "Serialized session_id "
                "is missing."
            )

        if not root_state_id:

            raise ValueError(
                "Serialized root_state_id "
                "is missing."
            )

        if not created_at_value:

            raise ValueError(
                "Serialized created_at "
                "is missing."
            )

        if not updated_at_value:

            raise ValueError(
                "Serialized updated_at "
                "is missing."
            )

        if not status_value:

            raise ValueError(
                "Serialized session status "
                "is missing."
            )

        try:

            status = SessionStatus(
                status_value
            )

        except ValueError as error:

            raise ValueError(
                "Unsupported session status: "
                f"{status_value}."
            ) from error

        graph = (
            StateGraphSerializer
            .deserialize(
                data.get(
                    "graph",
                    {},
                )
            )
        )

        cls._validate_root_state(
            root_state_id=(
                root_state_id
            ),

            graph=graph,
        )

        memory = (
            DomainSerializer
            .deserialize_memory(
                data.get(
                    "memory",
                    {},
                )
            )
        )

        failures_data = data.get(
            "failures",
            [],
        )

        if not isinstance(
            failures_data,
            list,
        ):

            raise ValueError(
                "Serialized failures must "
                "be a list."
            )

        failures = [
            DomainSerializer
            .deserialize_failure(
                failure_data
            )

            for failure_data
            in failures_data
        ]

        return ExplorationSessionSnapshot(
            schema_version=(
                schema_version
            ),

            session_id=(
                session_id
            ),

            root_state_id=(
                root_state_id
            ),

            status=status,

            created_at=(
                datetime.fromisoformat(
                    created_at_value
                )
            ),

            updated_at=(
                datetime.fromisoformat(
                    updated_at_value
                )
            ),

            graph=graph,

            memory=memory,

            failures=failures,
        )

    # =========================================================
    # VALIDATION
    # =========================================================

    @classmethod
    def _validate_schema_version(
        cls,
        schema_version,
    ) -> None:

        if (
            schema_version
            !=
            cls.CURRENT_SCHEMA_VERSION
        ):

            raise ValueError(
                "Unsupported session schema version: "
                f"{schema_version}. "
                "Expected: "
                f"{cls.CURRENT_SCHEMA_VERSION}."
            )

    @staticmethod
    def _validate_root_state(
        root_state_id: str,
        graph,
    ) -> None:

        if (
            graph.get_state(
                root_state_id
            )
            is None
        ):

            raise ValueError(
                "Session root state does not exist "
                "in StateGraph."
            )