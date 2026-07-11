"""
File: checkpoint_manager.py

Purpose:
    Manage durable checkpoints for one exploration session.

Architecture:

Live Exploration Runtime
    ├── StateGraph
    ├── ExplorationMemory
    └── FailureStore
            ↓
    CheckpointManager
            ↓
    ExplorationSessionSnapshot
            ↓
    Session Repository
            ↓
    Durable Storage
"""

from datetime import datetime

from core.graph.state_graph import (
    StateGraph,
)

from agent.memory.exploration_memory import (
    ExplorationMemory,
)

from agent.persistence.session_serializer import (
    SessionSerializer,
)

from agent.persistence.session_snapshot import (
    ExplorationSessionSnapshot,
)

from agent.persistence.session_status import (
    SessionStatus,
)


class CheckpointManager:
    """
    Manage durable checkpoints for one exploration session.

    The manager reads current runtime knowledge when each snapshot
    is created:

        - graph
        - memory
        - structured failure history

    Failure persistence remains optional for backward compatibility.
    """

    def __init__(
        self,
        session_id: str,
        root_state_id: str,
        graph: StateGraph,
        memory: ExplorationMemory,
        repository,
        created_at: datetime | None = None,
        status: SessionStatus = SessionStatus.CREATED,
        failure_store=None,
        clock=None,
    ) -> None:

        if (
            not isinstance(
                session_id,
                str,
            )
            or
            not session_id.strip()
        ):

            raise ValueError(
                "session_id must be a "
                "non-empty string."
            )

        if not isinstance(
            status,
            SessionStatus,
        ):

            raise ValueError(
                "status must be a "
                "SessionStatus."
            )

        if (
            not isinstance(
                root_state_id,
                str,
            )
            or
            not root_state_id.strip()
        ):

            raise ValueError(
                "root_state_id must be a "
                "non-empty string."
            )

        if (
            graph.get_state(
                root_state_id
            )
            is None
        ):

            raise ValueError(
                "root_state_id does not exist "
                "in the graph."
            )

        self.session_id = (
            session_id
        )

        self.root_state_id = (
            root_state_id
        )

        self.status = status

        self.graph = graph

        self.memory = memory

        self.failure_store = (
            failure_store
        )

        self.repository = repository

        self._clock = (
            clock
            or datetime.now
        )

        self.created_at = (
            created_at
            if created_at is not None
            else self._clock()
        )

        self.last_checkpoint_at = None

    # =========================================================
    # CHECKPOINT
    # =========================================================

    def checkpoint(
        self,
    ) -> ExplorationSessionSnapshot:

        updated_at = self._clock()

        snapshot = self.create_snapshot(
            updated_at=updated_at
        )

        self.repository.save(
            snapshot
        )

        self.last_checkpoint_at = (
            updated_at
        )

        return snapshot

    # =========================================================
    # SNAPSHOT CREATION
    # =========================================================

    def create_snapshot(
        self,
        updated_at: datetime | None = None,
    ) -> ExplorationSessionSnapshot:

        if updated_at is None:

            updated_at = self._clock()

        failures = []

        if (
            self.failure_store
            is not None
        ):

            failures = (
                self.failure_store.failures
            )

        return ExplorationSessionSnapshot(
            schema_version=(
                SessionSerializer
                .CURRENT_SCHEMA_VERSION
            ),

            session_id=(
                self.session_id
            ),

            root_state_id=(
                self.root_state_id
            ),

            status=(
                self.status
            ),

            created_at=(
                self.created_at
            ),

            updated_at=(
                updated_at
            ),

            graph=self.graph,

            memory=self.memory,

            failures=failures,
        )

    # =========================================================
    # SESSION LIFECYCLE
    # =========================================================

    def mark_running(
        self,
    ) -> ExplorationSessionSnapshot:

        self.status = (
            SessionStatus.RUNNING
        )

        return self.checkpoint()

    def mark_completed(
        self,
    ) -> ExplorationSessionSnapshot:

        self.status = (
            SessionStatus.COMPLETED
        )

        return self.checkpoint()

    def mark_failed(
        self,
    ) -> ExplorationSessionSnapshot:

        self.status = (
            SessionStatus.FAILED
        )

        return self.checkpoint()