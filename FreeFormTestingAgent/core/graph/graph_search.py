"""
graph/graph_search.py

Contains graph traversal algorithms used by the
Free Form Testing Agent.

Currently implemented:
    - Breadth First Search (BFS)

BFS is primarily used for:
    - Replay engine
    - Workflow reconstruction
    - Finding shortest path between states
    - Bug reproduction
"""

from collections import deque
from typing import Optional


class GraphSearch:
    """
    Collection of graph search algorithms.

    This class is stateless and only provides
    utility methods for traversing the StateGraph.
    """

    @staticmethod
    def bfs(
        graph,
        start_state: str,
        target_state: str
    ) -> Optional[list[str]]:
        """
        Find the shortest path between two states
        using Breadth First Search.

        Parameters
        ----------
        graph : StateGraph
            Graph instance containing states and transitions.

        start_state : str
            State ID from which search begins.

        target_state : str
            Desired destination state ID.

        Returns
        -------
        list[str]
            Ordered list of state IDs representing
            the shortest path.

        None
            Returned if no path exists.

        Example
        -------
        Graph:

            S0
             |
             7
             |
             S1
             |
             +
             |
             S2

        Call:

            bfs(graph, "S0", "S2")

        Returns:

            ["S0", "S1", "S2"]
        """

        # trivial case
        if start_state == target_state:
            return [start_state]

        # stores already explored states
        visited = set()

        # queue items:
        #
        # (
        #     current_state,
        #     path_taken
        # )
        queue = deque()

        # initialize search
        queue.append(
            (
                start_state,
                [start_state]
            )
        )

        while queue:

            # get next state to explore
            current_state, path = queue.popleft()

            # avoid processing state twice
            if current_state in visited:
                continue

            visited.add(current_state)

            # examine all outgoing transitions
            for transition in graph.edges.get(
                current_state,
                []
            ):

                next_state = transition.target_state

                # destination found
                if next_state == target_state:
                    return path + [next_state]

                # continue exploration
                queue.append(
                    (
                        next_state,
                        path + [next_state]
                    )
                )

        # path does not exist
        return None
    

    @staticmethod
    def bfs_transition_path(
        graph,
        start_state: str,
        target_state: str
    ) -> Optional[list]:
        """
        Find the shortest transition path between
        two states.

        Parameters
        ----------
        graph : StateGraph

        start_state : str

        target_state : str

        Returns
        -------
        list[Transition]
            Ordered list of transitions required
            to reach the target state.

        None
            If no path exists.

        Example
        -------

            S0 --7--> S1 --+--> S2

        returns

            [
                Transition(S0,S1,"7"),
                Transition(S1,S2,"+")
            ]
        """

        if start_state == target_state:
            return []

        visited = set()

        # queue:
        #
        # (
        #     current_state,
        #     transition_path
        # )
        queue = deque()

        queue.append(
            (
                start_state,
                []
            )
        )

        while queue:

            current_state, path = queue.popleft()

            if current_state in visited:
                continue

            visited.add(current_state)

            for transition in graph.edges.get(
                current_state,
                []
            ):

                next_state = transition.target_state

                new_path = path + [transition]

                if next_state == target_state:
                    return new_path

                queue.append(
                    (
                        next_state,
                        new_path
                    )
                )

        return None
