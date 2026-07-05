
from uuid import uuid4
from datetime import datetime
from pydantic import BaseModel, Field
from core.models.action_type import ActionType




class Action(BaseModel):
    action_id: str = Field(default_factory = lambda: str(uuid4()))
    action_type : ActionType
    target : str
    value : str | None= None
    timestamp: datetime = Field(default_factory = datetime.now)
    description : str | None = None

    def __str__(self):
        """
        Human readable representation.

        Example:
            CLICK(num7Button)
        """

        return (
            f"{self.action_type.value}"
            f"({self.target})"
        )