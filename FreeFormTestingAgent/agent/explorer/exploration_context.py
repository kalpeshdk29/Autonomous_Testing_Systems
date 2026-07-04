"""
File: exploration_context.py

Purpose:
    Stores runtime exploration state.

Architecture:

Explorer
    ↓
ExplorationContext
        ├── queue
        ├── visited states
        ├── statistics
        └── discovered states
"""

from collections import deque


class ExplorationContext:
    """
    Stores current exploration session information.

    Example
    -------

        queue:
            [S0,S1,S2]

        visited:
            {
                S0,
                S1
            }

        statistics:
            states=25
            actions=200
            transitions=45
    """

    def __init__(self):
        """
        Initialize exploration context.
        """
        #
        # BFS queue
        #
        self.state_queue = deque()

        #
        # Already explored states
        #
        self.visited_states = set()

        #
        # Statistics
        #
        self.total_states = 0

        self.total_actions = 0

        self.total_transitions = 0
        
        #
        # Number of failed action executions.
        #
        self.total_failures = 0

        #
        # Reason why exploration stopped.
        #
        self.stop_reason = None

    def enqueue(
        self,
        state_id: str
    ):
        """
        Add state to exploration queue.
        """

        self.state_queue.append(
            state_id
        )

    def dequeue(
        self
    ) -> str:
        """
        Get next state to explore.
        """

        return self.state_queue.popleft()

    def has_states(
        self
    ) -> bool:
        """
        Check whether queue has states.
        """

        return len(
            self.state_queue
        ) > 0