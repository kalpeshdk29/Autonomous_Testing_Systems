

class WindowsRecoveryAdapter():

    def __init__(
        self,
        ui_adapter,
    ):
        self._ui = ui_adapter

    def launch(
        self,
        executable,
    ):
        return self._ui.launch_application(
            executable
        )

    def connect(
        self,
        window_title,
    ):
        return self._ui.connect_window(
            window_title
        )