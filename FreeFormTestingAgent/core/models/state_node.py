"""
File: state_node.py

Purpose:
    Wrap an ApplicationState with graph-specific metadata.

Architecture:

ApplicationState
        +
Graph Metadata
        ↓
StateNode

Why This Component Exists:
    ApplicationState represents the observed application.

    StateNode represents that state inside the graph.

    Graph-specific information such as:

        - visit count
        - discovery depth

    belongs to StateNode rather than ApplicationState.
"""

from core.models.state import ApplicationState


class StateNode:
    """
    Represents an application state inside the StateGraph.

    Attributes
    ----------
    state:
        The captured ApplicationState.

    visits:
        Number of times this state has been encountered.

    depth:
        Shortest known distance from the exploration root.

        Example:

            Root        depth = 0

            Child       depth = 1

            Grandchild  depth = 2

    Important
    ---------
    Depth represents the shortest known path from the root.

    A state may first be discovered through a long path and
    later through a shorter path.

    Therefore, depth may be updated when a shorter path is
    discovered.
    """

    def __init__(self, state: ApplicationState, depth: int = 0):
        """
        Create a graph state node.

        Parameters
        ----------
        state:
            Application state stored by this node.

        depth:
            Shortest known distance from the root state.
        """

        self.state = state

        self.visits = 1

        self.depth = depth

    def visit(self):
        """
        Record another encounter with this state.
        """

        self.visits += 1

    def update_depth(self, new_depth: int) -> bool:
        """
        Update the node depth only when a shorter path
        has been discovered.

        Parameters
        ----------
        new_depth:
            Newly discovered candidate depth.

        Returns
        -------
        bool:
            True:
                Depth was updated.

            False:
                Existing depth was already shorter
                or equal.

        Example
        -------

            Current depth = 3

            New path depth = 1

            Result:

                depth = 1
                return True
        """

        if new_depth < self.depth:

            self.depth = new_depth

            return True

        return False
