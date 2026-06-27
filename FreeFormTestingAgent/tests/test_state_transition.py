"""
Test:
    Verify that calculator state changes
    after clicking a button.
"""

from adapters.ui.windows_ui import WindowsUIAdapter
from agent.executor.action_executor import ActionExecutor


ui = WindowsUIAdapter()

# Launch calculator
ui.launch_application("calc.exe")

# Connect to calculator window
window = ui.connect_window("Calculator")

# Capture initial state
state = ui.capture_state(window)

print("\nINITIAL STATE:")
print(state.values)

# Find the "7" button action
action_for_num7 = next(
    action
    for action in state.available_actions
    if action.target == "num7Button"
)

# Execute action
executor = ActionExecutor()

executor.execute(
    window,
    action_for_num7
)

# Capture new state
state = ui.capture_state(window)

print("\nNEW STATE:")
print(state.values)