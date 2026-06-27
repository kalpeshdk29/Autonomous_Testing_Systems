from enum import Enum
from uuid import uuid4
from datetime import datetime
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    CLICK = "CLICK"
    DOUBLE_CLICK = "DOUBLE_CLICK"
    TEXT_INPUT = "TEXT_INPUT"
    KEY_PRESS = "KEY_PRESS"
    HOTKEY = "HOTKEY"
    SCROLL = "SCROLL"
    WAIT = "WAIT"


class Action(BaseModel):
    action_id: str = Field(default_factory = lambda: str(uuid4()))
    action_type : ActionType
    target : str
    value : str | None= None
    timestamp: datetime = Field(default_factory = datetime.now)
    description : str | None = None