# graph/models/state_node.py

from dataclasses import dataclass
from core.models.state import ApplicationState



@dataclass
class StateNode:

    state: ApplicationState

    visits: int = 1

    explored: bool = False

    depth: int = 0

    def visit(self):
        self.visits += 1