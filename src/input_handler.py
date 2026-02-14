import threading
import time
from typing import Dict, Any
from pynput import mouse


class InputHandler:
    def __init__(self):
        self.mouse_controller = mouse.Controller()
        self.desktop_width = 1920
        self.desktop_height = 1080
        self.lock = threading.Lock()
        self.last_action_time = 0
        self.min_action_interval = 0.005
        self.button_state: Dict[str, bool] = {
            "left": False,
            "right": False,
            "middle": False,
        }

    def set_desktop_size(self, width: int, height: int):
        with self.lock:
            self.desktop_width = width
            self.desktop_height = height

    def process_event(
        self, event: Dict[str, Any], client_width: int, client_height: int
    ):
        event_type = event.get("type")

        self._rate_limit()

        if event_type == "move":
            self._handle_move(event, client_width, client_height)
        elif event_type == "click":
            self._handle_click(event)
        elif event_type == "mousedown":
            self._handle_mousedown(event)
        elif event_type == "mouseup":
            self._handle_mouseup(event)
        elif event_type == "scroll":
            self._handle_scroll(event)

    def _rate_limit(self):
        elapsed = time.time() - self.last_action_time
        if elapsed < self.min_action_interval:
            time.sleep(self.min_action_interval - elapsed)
        self.last_action_time = time.time()

    def _transform_coordinates(
        self, x: float, y: float, client_width: int, client_height: int
    ) -> tuple[int, int]:
        with self.lock:
            pc_x = int((x / client_width) * self.desktop_width)
            pc_y = int((y / client_height) * self.desktop_height)
            pc_x = max(0, min(pc_x, self.desktop_width - 1))
            pc_y = max(0, min(pc_y, self.desktop_height - 1))
            return pc_x, pc_y

    def _handle_move(
        self, event: Dict[str, Any], client_width: int, client_height: int
    ):
        x = event.get("x", 0)
        y = event.get("y", 0)
        pc_x, pc_y = self._transform_coordinates(x, y, client_width, client_height)
        self.mouse_controller.position = (pc_x, pc_y)

    def _handle_click(self, event: Dict[str, Any]):
        button_name = event.get("button", "left")
        count = event.get("count", 1)
        button = self._get_button(button_name)
        self.mouse_controller.click(button, count)

    def _handle_mousedown(self, event: Dict[str, Any]):
        button_name = event.get("button", "left")
        button = self._get_button(button_name)
        if not self.button_state.get(button_name, False):
            self.mouse_controller.press(button)
            self.button_state[button_name] = True

    def _handle_mouseup(self, event: Dict[str, Any]):
        button_name = event.get("button", "left")
        button = self._get_button(button_name)
        if self.button_state.get(button_name, False):
            self.mouse_controller.release(button)
            self.button_state[button_name] = False

    def _handle_scroll(self, event: Dict[str, Any]):
        dx = event.get("dx", 0)
        dy = event.get("dy", 0)
        self.mouse_controller.scroll(dx, dy)

    def _get_button(self, name: str) -> mouse.Button:
        buttons = {
            "left": mouse.Button.left,
            "right": mouse.Button.right,
            "middle": mouse.Button.middle,
        }
        return buttons.get(name, mouse.Button.left)

    def release_all(self):
        for button_name in self.button_state:
            if self.button_state[button_name]:
                button = self._get_button(button_name)
                self.mouse_controller.release(button)
                self.button_state[button_name] = False
