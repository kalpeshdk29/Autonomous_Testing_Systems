from pydantic import BaseModel


class UIControl(BaseModel):

    automation_id: str = ""

    name: str = ""

    control_type: str = ""

    class_name: str = ""

    depth: int = 0