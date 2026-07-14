"""
File:
    exploration_summary.py

Purpose:
    Produce a human-readable summary of a completed
    application knowledge extraction session.
"""

from datetime import timedelta


class ExplorationSummary:

    @staticmethod
    def print(
        graph,
        memory,
        coordinator_result,
    ):

        total_states = len(
            graph.states
        )

        total_transitions = sum(
            len(edges)
            for edges in graph.edges.values()
        )

        successful = 0
        failed = 0

        for edges in graph.edges.values():

            for transition in edges:

                if transition.success:

                    successful += 1

                else:

                    failed += 1

        explored = memory.total_explored_actions()

        remaining = memory.total_remaining_actions()

        duration = timedelta(
            seconds=int(
                coordinator_result.duration
            )
        )

        print()

        print("=" * 60)
        print(
            "APPLICATION KNOWLEDGE EXTRACTION COMPLETE"
        )
        print("=" * 60)

        print()

        print(
            f"States              : {total_states}"
        )

        print(
            f"Transitions         : {total_transitions}"
        )

        print(
            f"Successful          : {successful}"
        )

        print(
            f"Failed              : {failed}"
        )

        print()

        print(
            f"Explored Actions    : {explored}"
        )

        print(
            f"Remaining Actions   : {remaining}"
        )

        print()

        print(
            f"Coordinator Steps   : "
            f"{coordinator_result.steps}"
        )

        print(
            f"Failures            : "
            f"{coordinator_result.failed_steps}"
        )

        print(
            f"Duration            : {duration}"
        )

        print()

        print("=" * 60)