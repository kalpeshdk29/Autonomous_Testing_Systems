"""
File: session_snapshot.py

Purpose:
    Represent one complete durable exploration session in memory.

Architecture:

Exploration Runtime
        ↓
Graph + Memory + Root State + Metadata
        ↓
ExplorationSessionSnapshot

Important:
    This object does not read or write files.

    It represents the complete runtime state required to save
    and later resume an exploration session.
"""

from dataclasses import dataclass
from datetime import datetime

from core.graph.state_graph import StateGraph

from agent.memory.exploration_memory import (
    ExplorationMemory,
)


@dataclass
class ExplorationSessionSnapshot:
    """
    Complete runtime snapshot of one exploration session.

    Attributes
    ----------
    schema_version:
        Persistence schema version used by this snapshot.

    session_id:
        Stable identifier for the exploration session.

    root_state_id:
        Root state used for replay and continuation.

    created_at:
        Time when the session was originally created.

    updated_at:
        Time represented by this snapshot.

    graph:
        Complete exploration StateGraph.

    memory:
        Complete ExplorationMemory.
    """

    schema_version: int

    session_id: str

    root_state_id: str

    created_at: datetime

    updated_at: datetime

    graph: StateGraph

    memory: ExplorationMemory