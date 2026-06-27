"""
File: transition_engine.py

Purpose:
    Creates state transitions after actions
    are executed.

Architecture:

State A
    +
Action
    =
State B
"""

import time

from core.models.transition import Transition
from core.state.state_hasher import create_state_hash


class TransitionEngine:
    """
    Creates transitions between application states.
    """

    def create_transition(
            self,
            source_state,
            action,
            target_state,
            success=True,
            duration=0.0
    ) -> Transition:
        """
        Create a transition between two states.

        Args:
            source_state:
                State before execution.

            action:
                Executed action.

            target_state:
                State after execution.

        Returns:
            Transition object.
        """

        return Transition(
            source_state=source_state.state_hash,
            target_state=target_state.state_hash,
            action=action,
            success=success,
            duration=duration
        )