from enum import Enum

class ActionType(str, Enum):
    CLICK = "CLICK"
    DOUBLE_CLICK = "DOUBLE_CLICK"
    TEXT_INPUT = "TEXT_INPUT"
    KEY_PRESS = "KEY_PRESS"
    HOTKEY = "HOTKEY"
    SCROLL = "SCROLL"
    WAIT = "WAIT"