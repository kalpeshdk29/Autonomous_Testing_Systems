# adapters/ui/windows_ui.py

import subprocess
import time
import uiautomation as auto

from core.models.state import ApplicationState

class WindowsUIAdapter:

    def launch_application(
        self,
        executable: str
    ):

        process = subprocess.Popen(executable)

        time.sleep(3)

        return process


    def connect_window(
        self,
        window_name: str
    ):

        window = auto.WindowControl(
            Name=window_name
        )

        if not window.Exists():
            raise Exception(
                f"Window not found: {window_name}"
            )

        return window


    def get_controls(
        self,
        window
    ):
        return self.get_all_controls(window)


    def capture_state(
        self,
        window
    ):

        controls = self.get_controls(window)

        state = ApplicationState(
            window_title=window.Name,
            controls=controls
        )

        return state

    def get_all_controls(
            self,
            control,
            depth=0,
            max_depth=10):

        controls = []

        if depth > max_depth:
            return controls

        try:

            controls.append(
                {
                    "automation_id":
                        control.AutomationId,

                    "name":
                        control.Name,

                    "type":
                        control.ControlTypeName,

                    "class":
                        control.ClassName,

                    "depth":
                        depth
                }
            )

        except Exception:
            pass

        try:

            for child in control.GetChildren():

                controls.extend(
                    self.get_all_controls(
                        child,
                        depth + 1,
                        max_depth
                    )
                )

        except Exception:
            pass

        return controls