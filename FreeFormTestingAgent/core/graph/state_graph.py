"""
File: state_graph.py

Purpose:
    Stores discovered application states and transitions.

Architecture:

State
    +
Transition
        ↓
StateGraph
"""

from core.models.state_node import StateNode
from core.models.state import ApplicationState
from core.models.transition import Transition
from core.graph.graph_search import GraphSearch
import uuid

class StateGraph:
    """
    Stores the explored application state space.

    Responsibilities:
        - Store states
        - Store transitions
        - Detect duplicate states
        - Provide exploration history
    """

    def __init__(self):

         # state_id -> StateNode
        self.states = {}

        # hash -> state_id
        self.hash_index = {}

        # source_state -> list[Transition]
        self.edges = {}

    def add_state(
        self,
        state: ApplicationState,
        depth: int = 0
    ) -> str:
        """
        Add an application state to the graph.

        Parameters
        ----------
        state:
            Application state to store.

        depth:
            Candidate depth of the state.

            Root state:

                depth = 0

            Child state:

                source depth + 1

        Returns
        -------
        str:
            ID of the stored state.

        Behavior
        --------
        New state:
            Create a StateNode using the provided depth.

        Existing state:
            Increment visit count.

            Update depth only when the newly discovered
            path is shorter.
        """

        # =====================================================
        # CASE 1
        # State already exists
        # =====================================================

        if state.state_hash in self.hash_index:

            state_id = self.hash_index[
                state.state_hash
            ]

            node = self.states[
                state_id
            ]

            #
            # Record another encounter.
            #
            node.visit()

            #
            # Preserve the shortest known depth.
            #
            node.update_depth(
                depth
            )

            return state_id

        # =====================================================
        # CASE 2
        # New state
        # =====================================================

        node = StateNode(
            state,
            depth=depth
        )

        self.states[
            state.state_id
        ] = node

        self.hash_index[
            state.state_hash
        ] = state.state_id

        self.edges[
            state.state_id
        ] = []

        return state.state_id
        
    def add_transition(
        self,
        source_id,
        action,
        target_id,
        success=True,
        duration=0.0):

        transition = Transition(
            source_state=source_id,
            target_state=target_id,
            action=action,
            success=success,
            duration=duration
        )

        self.edges[source_id].append(transition)

        return transition

    def has_state(
            self,
            state_hash: str
    ) -> bool:
        """
        Check if state already exists.
        """

        return state_hash in self.hash_index

    def get_state(self, state_id):

        return self.states.get(state_id)

    def get_neighbors(self, state_id):

        return [
            t.target_state
            for t in self.edges.get(state_id, [])
        ]

    def print_graph(self):

        print("\n===== GRAPH =====\n")

        for source, transitions in self.edges.items():

            print(source)

            for t in transitions:

                print(
                    f"   --{t.action}--> "
                    f"{t.target_state}"
                )

    def find_path(
        self,
        source_state: str,
        target_state: str
    ) -> list[str] | None:
        """
        Find shortest path between two states.

        Parameters
        ----------
        source_state : str
            Starting state ID.

        target_state : str
            Destination state ID.

        Returns
        -------
        list[str]
            Ordered list of state IDs.

        None
            If no path exists.

        Example
        -------

            S0 -> S1 -> S2 -> S3

        returns:

            ["S0","S1","S2","S3"]
        """

        return GraphSearch.bfs(
            self,
            source_state,
            target_state
        )
    
    def get_state_depth(
        self,
        state_id: str
    ) -> int | None:
        """
        Return the shortest known depth of a state.

        Parameters
        ----------
        state_id:
            ID of the graph state.

        Returns
        -------
        int:
            State depth.

        None:
            State does not exist.
        """

        node = self.get_state(
            state_id
        )

        if node is None:
            return None

        return node.depth

    def update_state_depth(
        self,
        state_id: str,
        depth: int
    ) -> bool:
        """
        Attempt to update a state's depth.

        The depth is changed only when the provided depth
        is shorter than the currently known depth.

        Returns
        -------
        bool:
            True when depth changed.

            False when:
                - state does not exist
                - existing depth is already shorter
                - depths are equal
        """

        node = self.get_state(
            state_id
        )

        if node is None:
            return False

        return node.update_depth(
            depth
        )

    def find_transition_path(
        self,
        source_state: str,
        target_state: str
    ):
        """
        Find shortest transition sequence between
        two states.

        Returns
        -------
        list[Transition]
            Ordered transitions.

        Example
        -------

            S0 --7--> S1 --+--> S2

        returns

            [
                Transition(...),
                Transition(...)
            ]
        """

        return GraphSearch.bfs_transition_path(
            self,
            source_state,
            target_state
        )