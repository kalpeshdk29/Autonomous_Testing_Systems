"""
Exports StateGraph into GraphViz DOT format.
"""


class GraphVizExporter:

    @staticmethod
    def export(
        graph,
        output_path,
    ):

        with open(
            output_path,
            "w",
            encoding="utf-8",
        ) as f:

            f.write("digraph Application {\n")

            f.write(
                'rankdir="LR";\n'
            )

            f.write(
                'node [shape=box, style=rounded];\n\n'
            )

            #
            # Nodes
            #
            for state_id, node in graph.states.items():

                label = (
                    f"{state_id[:8]}\\n"
                    f"Depth:{node.depth}"
                )

                f.write(

                    f'"{state_id}" '

                    f'[label="{label}"];\n'
                )

            f.write("\n")

            #
            # Edges
            #
            for transitions in graph.edges.values():

                for transition in transitions:

                    action = (
                        transition.action.target
                    )

                    color = (
                        "green"
                        if transition.success
                        else "red"
                    )

                    label = action

                    if transition.failure_reason:

                        label += (
                            "\\n"
                            + transition.failure_reason
                        )

                    f.write(

                        f'"{transition.source_state}" '

                        f'-> '

                        f'"{transition.target_state}" '

                        f'[label="{label}", '

                        f'color="{color}"];\n'
                    )

            f.write("}\n")