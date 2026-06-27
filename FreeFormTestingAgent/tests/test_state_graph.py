"""
Test:

S0
 |
Click(7)
 |
S1

Store everything in graph.
"""

import time

from adapters.ui.windows_ui import WindowsUIAdapter

from agent.executor.action_executor import (
    ActionExecutor
)

from agent.explorer.transition_engine import (
    TransitionEngine
)

from core.graph.state_graph import (
    StateGraph
)

from core.state.state_hasher import (
    create_state_hash
)


ui = WindowsUIAdapter()

ui.launch_application(
    "calc.exe"
)

window = ui.connect_window(
    "Calculator"
)

graph = StateGraph()

#
# Capture initial state
#
state_before = ui.capture_state(
    window
)

state_before.state_hash = (
    create_state_hash(
        state_before
    )
)

graph.add_state(
    state_before
)

#
# Find action
#
action = next(
    a
    for a in state_before.available_actions
    if a.target == "num7Button"
)

#
# Execute action
#
executor = ActionExecutor()

start = time.time()

success = executor.execute(
    window,
    action
)

duration = (
    time.time()
    - start
)

#
# Capture new state
#
state_after = ui.capture_state(
    window
)

state_after.state_hash = (
    create_state_hash(
        state_after
    )
)

graph.add_state(
    state_after
)

#
# Create transition
#
engine = TransitionEngine()

transition = (
    engine.create_transition(
        state_before,
        action,
        state_after,
        success,
        duration
    )
)

graph.add_transition(
    transition
)

#
# Print graph
#
graph.print_graph()