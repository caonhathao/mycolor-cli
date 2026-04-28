from typing import Any


class BaseTab:
    def __init__(self, parent):
        self.parent = parent

    def update(self, current_time: float) -> bool:
        raise NotImplementedError

    def render(self) -> Any:
        raise NotImplementedError

    def on_activate(self):
        pass

    def on_deactivate(self):
        pass
