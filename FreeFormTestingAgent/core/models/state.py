from uuid import uuid4
from datetime import datetime
from pydantic import BaseModel, Field
from core.models.ui_control import UIControl
from core.models.action import Action


class ApplicationState(BaseModel):

    state_id: str = Field(
        default_factory=lambda: str(uuid4())
    )

    timestamp: datetime = Field(
        default_factory=datetime.now
    )

    window_title: str = ""

    controls: list[UIControl] = []

    values: dict = {}

    available_actions: list[Action] = []

    screenshot_path: str | None = None

    metadata: dict = {}

    state_hash: str | None = None