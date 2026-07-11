"""
File: session_snapshot.py

Purpose:
    Represent one complete durable exploration session in memory.

Architecture:

Exploration Runtime
        ↓
Graph
+
Memory
+
Failure History
+
Root State
+
Lifecycle
+
Metadata
        ↓
ExplorationSessionSnapshot

Important:
    This object does not read or write files.

    It represents the complete runtime knowledge required to save
    and later resume an exploration session.
"""

from dataclasses import dataclass, field
from datetime import datetime

from core.graph.state_graph import (
    StateGraph,
)

from agent.failure.failure_record import (
    FailureRecord,
)

from agent.memory.exploration_memory import (
    ExplorationMemory,
)

from agent.persistence.session_status import (
    SessionStatus,
)


@dataclass
class ExplorationSessionSnapshot:
    """
    Complete durable snapshot of one exploration session.

    Attributes
    ----------
    schema_version:
        Persistence schema version.

    session_id:
        Stable exploration session identifier.

    root_state_id:
        Root state used for replay and continuation.

    status:
        Durable lifecycle state.

    created_at:
        Original session creation time.

    updated_at:
        Time represented by this snapshot.

    graph:
        Complete exploration StateGraph.

    memory:
        Complete ExplorationMemory.

    failures:
        Ordered structured failure history discovered during the
        session.

        A default empty list preserves compatibility with older
        construction sites that do not yet supply failures.
    """

    schema_version: int

    session_id: str

    root_state_id: str

    status: SessionStatus

    created_at: datetime

    updated_at: datetime

    graph: StateGraph

    memory: ExplorationMemory

    failures: list[
        FailureRecord
    ] = field(
        default_factory=list
    )

    @property
    def was_interrupted(
        self,
    ) -> bool:
        """
        Return whether this snapshot represents an unfinished
        previous execution.

        A persisted RUNNING session loaded by a new runtime means
        the previous process stopped before recording a clean
        terminal status.
        """

        return (
            self.status
            ==
            SessionStatus.RUNNING
        )