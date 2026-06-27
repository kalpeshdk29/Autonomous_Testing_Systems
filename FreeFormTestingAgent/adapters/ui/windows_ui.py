# adapters/ui/windows_ui.py

import subprocess
import time
import uiautomation as auto
from core.models.state import ApplicationState
from core.models.ui_control import UIControl
from agent.explorer.action_discovery import ActionDiscovery




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

        controls = self.get_controls(
            window
        )

        values = self.get_values(
            controls
        )

        state = ApplicationState(
            window_title=window.Name,
            controls=controls,
            values=values
        )

        discover = ActionDiscovery()

        state.available_actions = (
            discover.discover(
                state.controls
            )
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
                        UIControl(
                            automation_id=
                                control.AutomationId,

                            name=
                                control.Name,

                            control_type=
                                control.ControlTypeName,

                            class_name=
                                control.ClassName,

                            depth=depth
                        )
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
    
    """
    Extract dynamic application values from the UI.

    These values become part of the ApplicationState and
    are used for state comparison and hashing.
    """
    def get_values(
            self,
            controls
    ) -> dict:

        values = {}

        for control in controls:

            # Calculator expression
            if control.automation_id == "CalculatorExpression":

                values["expression"] = (
                    control.name
                )

            # Calculator display
            elif control.automation_id == "CalculatorResults":

                values["display"] = (
                    control.name
                )

            # Raw numeric output
            elif control.automation_id == "NormalOutput":

                values["output"] = (
                    control.name
                )

        return values