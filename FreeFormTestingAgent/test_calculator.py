
from adapters.ui.windows_ui import WindowsUIAdapter
ui = WindowsUIAdapter()

app = ui.launch_application('calc.exe')

print("App: " , app)