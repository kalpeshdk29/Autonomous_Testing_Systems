from adapters.ui.windows_ui import WindowsUIAdapter
ui = WindowsUIAdapter()

ui.launch_application("calc.exe")

window = ui.connect_window("Calculator")

controls = ui.get_controls(window)

print()
print("TOTAL:", len(controls))

for c in controls:
    print(c)