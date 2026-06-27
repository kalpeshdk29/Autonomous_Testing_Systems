"""
File: exploration_memory.py

Purpose:
    Store which actions have already been executed
    for each discovered state.

Architecture:

State Hash
        ↓
Executed Actions
"""

from collections import defaultdict


class ExplorationMemory:
    """
    Stores exploration history.

    Example:

        {
            state_hash_1:
                {
                    "num7Button",
                    "plusButton"
                },

            state_hash_2:
                {
                    "num8Button"
                }
        }
    """

    def __init__(self):
        """
        Initialize memory storage.
        """

        self.visited_actions = defaultdict(set)

    def mark_executed(
            self,
            state_hash: str,
            action_target: str
    ):
        """
        Mark an action as executed for a state.

        Args:
            state_hash:
                Current state hash.

            action_target:
                Action target identifier.
        """

        self.visited_actions[
            state_hash
        ].add(
            action_target
        )

    def is_executed(
            self,
            state_hash: str,
            action_target: str
    ) -> bool:
        """
        Check if action was already executed.
        """

        return (
            action_target
            in
            self.visited_actions[
                state_hash
            ]
        )

    def get_unexplored_actions(
            self,
            state_hash: str,
            actions
    ):
        """
        Return actions that have not been executed yet.

        Args:
            state_hash:
                Current state.

            actions:
                Available actions.

        Returns:
            List of unexplored actions.
        """

        unexplored = []

        for action in actions:

            if not self.is_executed(
                    state_hash,
                    action.target):

                unexplored.append(
                    action
                )

        return unexplored