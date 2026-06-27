from adapters.ui.windows_ui import WindowsUIAdapter


ui = WindowsUIAdapter()

ui.launch_application("calc.exe")

window = ui.connect_window(
    "Calculator"
)

state = ui.capture_state(
    window
)

print()
print("ACTIONS")
print()

for c in state.controls:
    if "Text" in c.control_type:
        print(c)