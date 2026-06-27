from adapters.ui.windows_ui import (
    WindowsUIAdapter
)

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

print()

print(
    "VALUES:"
)

for key, value in (
        state.values.items()):

    print(
        key,
        "=",
        value
    )

