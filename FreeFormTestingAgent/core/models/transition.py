from datetime import datetime
from pydantic import BaseModel

from core.models.action import Action


class Transition(BaseModel):

    source_state: str

    target_state: str

    action: Action

    success: bool = True

    duration: float = 0.0

    timestamp: datetime = datetime.now()