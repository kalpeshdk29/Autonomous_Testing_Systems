"""
Test:
    Launch calculator
    Discover actions
    Execute a known action
"""

from adapters.ui.windows_ui import WindowsUIAdapter
from agent.executor.action_executor import ActionExecutor


ui = WindowsUIAdapter()

ui.launch_application(
    "calc.exe"
)

window = ui.connect_window(
    "Calculator"
)

state = ui.capture_state(
    window
)

executor = ActionExecutor()

# Find "Seven" button
action = next(
    a for a in state.available_actions
    if a.target == "num7Button"
)

print()
print(
    f"Executing: "
    f"{action.description}"
)

success = executor.execute(
    window,
    action
)

print()
print(
    f"Success: "
    f"{success}"
)