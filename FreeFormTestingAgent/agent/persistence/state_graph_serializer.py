"""
File: state_graph_serializer.py

Purpose:
    Convert StateGraph runtime objects into JSON-compatible data
    and reconstruct an equivalent usable StateGraph.

Architecture:

StateGraph
    ↓
States + StateNode Metadata + Transitions
    ↓
JSON-Compatible Dictionary

JSON-Compatible Dictionary
    ↓
Reconstruct States and Indexes
    ↓
Reconstruct Transitions
    ↓
Usable StateGraph

Important:
    This component does not read or write files.

    Filesystem persistence belongs to the future
    JsonSessionRepository.
"""

from core.graph.state_graph import StateGraph
from core.models.state_node import StateNode

from agent.persistence.domain_serializer import (
    DomainSerializer,
)


class StateGraphSerializer:
    """
    Serialize and deserialize StateGraph.

    Preserved runtime information:

        - ApplicationState data
        - StateNode depth
        - StateNode visits
        - hash_index behavior
        - graph edges
        - Transition data
    """

    # =========================================================
    # SERIALIZATION
    # =========================================================

    @staticmethod
    def serialize(
        graph: StateGraph,
    ) -> dict:
        """
        Convert StateGraph into JSON-compatible data.

        States and transitions are emitted in deterministic order
        so snapshots remain easy to inspect and compare.
        """

        states = []

        for state_id in sorted(graph.states.keys()):

            node = graph.states[state_id]

            states.append(
                {
                    "state_id": state_id,
                    "depth": node.depth,
                    "visits": node.visits,
                    "state": (DomainSerializer.serialize_state(node.state)),
                }
            )

        transitions = []

        for source_state_id in sorted(graph.edges.keys()):

            for transition in graph.edges[source_state_id]:

                transitions.append(DomainSerializer.serialize_transition(transition))

        return {
            "states": states,
            "transitions": transitions,
        }

    # =========================================================
    # DESERIALIZATION
    # =========================================================

    @staticmethod
    def deserialize(
        data: dict,
    ) -> StateGraph:
        """
        Reconstruct a complete usable StateGraph.

        Loading is intentionally performed without add_state().

        add_state() represents runtime exploration behavior:

            existing state
                → increment visits
                → maybe shorten depth

        Persistence loading must instead restore the exact saved
        snapshot without creating artificial encounters.
        """

        graph = StateGraph()

        # =====================================================
        # STEP 1
        # Restore states and graph indexes
        # =====================================================

        for state_record in data.get(
            "states",
            [],
        ):

            state = DomainSerializer.deserialize_state(state_record["state"])

            saved_state_id = state_record["state_id"]

            if state.state_id != saved_state_id:

                raise ValueError(
                    "Serialized graph state ID does not match "
                    "ApplicationState.state_id."
                )

            node = StateNode(
                state,
                depth=state_record.get(
                    "depth",
                    0,
                ),
            )

            node.visits = state_record.get(
                "visits",
                1,
            )

            graph.states[saved_state_id] = node

            graph.hash_index[state.state_hash] = saved_state_id

            graph.edges[saved_state_id] = []

        # =====================================================
        # STEP 2
        # Restore transitions
        # =====================================================

        for transition_data in data.get(
            "transitions",
            [],
        ):

            transition = DomainSerializer.deserialize_transition(transition_data)

            if transition.source_state not in graph.states:

                raise ValueError(
                    "Transition source state does not exist " "in serialized graph."
                )

            if transition.target_state not in graph.states:

                raise ValueError(
                    "Transition target state does not exist " "in serialized graph."
                )

            graph.edges[transition.source_state].append(transition)

        return graph
