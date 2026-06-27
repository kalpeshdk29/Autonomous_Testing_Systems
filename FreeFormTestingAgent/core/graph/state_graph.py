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

from core.models.state import ApplicationState
from core.models.transition import Transition


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

        # state_hash -> ApplicationState
        self.states = {}

        # list of transitions
        self.transitions = []

    def add_state(
            self,
            state: ApplicationState
    ):
        """
        Add a state to the graph.

        Duplicate states are ignored.
        """

        self.states[
            state.state_hash
        ] = state

    def add_transition(
            self,
            transition: Transition
    ):
        """
        Add a transition to the graph.
        """

        self.transitions.append(
            transition
        )

    def has_state(
            self,
            state_hash: str
    ) -> bool:
        """
        Check if state already exists.
        """

        return (
            state_hash
            in self.states
        )

    def print_graph(self):
        """
        Print the discovered state graph.
        """

        print("\n===== STATES =====\n")

        for state in self.states.values():

            print(
                state.state_hash[:8],
                state.values
            )

        print("\n===== TRANSITIONS =====\n")

        for transition in self.transitions:

            print(
                f"{transition.source_state[:8]}"
                f" -- "
                f"{transition.action.description}"
                f" --> "
                f"{transition.target_state[:8]}"
            )