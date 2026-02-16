import threading
import time
from typing import Dict, Any, Optional, Union
from pynput import mouse, keyboard
import logging


class InputHandler:
    def __init__(self):
        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()
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
        self.key_state: Dict[str, bool] = {}
        self.logger = logging.getLogger("opentouch.input")

    def set_desktop_size(self, width: int, height: int):
        with self.lock:
            self.desktop_width = width
            self.desktop_height = height
            self.logger.debug(f"Desktop size set to {width}x{height}")

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
        elif event_type == "keydown":
            self._handle_keydown(event)
        elif event_type == "keyup":
            self._handle_keyup(event)
        elif event_type == "keypress":
            self._handle_keypress(event)

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
        self.logger.debug(f"Click: {button_name} x{count}")

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
        scroll_units = int(dy * 2)
        self.mouse_controller.scroll(dx, scroll_units)

    def _handle_keydown(self, event: Dict[str, Any]):
        key = event.get("key", "")
        if not key:
            return
        try:
            key_obj = self._parse_key(key)
            if key_obj and not self.key_state.get(key, False):
                self.keyboard_controller.press(key_obj)
                self.key_state[key] = True
                self.logger.debug(f"KeyDown: {key}")
        except Exception as e:
            self.logger.debug(f"KeyDown error for '{key}': {e}")

    def _handle_keyup(self, event: Dict[str, Any]):
        key = event.get("key", "")
        if not key:
            return
        try:
            key_obj = self._parse_key(key)
            if key_obj and self.key_state.get(key, False):
                self.keyboard_controller.release(key_obj)
                self.key_state[key] = False
                self.logger.debug(f"KeyUp: {key}")
        except Exception as e:
            self.logger.debug(f"KeyUp error for '{key}': {e}")

    def _handle_keypress(self, event: Dict[str, Any]):
        key = event.get("key", "")
        if not key:
            return
        try:
            if len(key) == 1:
                self.keyboard_controller.tap(key)
                self.logger.debug(f"KeyPress: {key}")
        except Exception as e:
            self.logger.debug(f"KeyPress error for '{key}': {e}")

    def _parse_key(self, key: str) -> Optional[Union[keyboard.Key, keyboard.KeyCode]]:
        special_keys = {
            "enter": keyboard.Key.enter,
            "tab": keyboard.Key.tab,
            "escape": keyboard.Key.esc,
            "esc": keyboard.Key.esc,
            "backspace": keyboard.Key.backspace,
            "delete": keyboard.Key.delete,
            "space": keyboard.Key.space,
            "arrow_up": keyboard.Key.up,
            "arrow_down": keyboard.Key.down,
            "arrow_left": keyboard.Key.left,
            "arrow_right": keyboard.Key.right,
            "up": keyboard.Key.up,
            "down": keyboard.Key.down,
            "left": keyboard.Key.left,
            "right": keyboard.Key.right,
            "home": keyboard.Key.home,
            "end": keyboard.Key.end,
            "page_up": keyboard.Key.page_up,
            "page_down": keyboard.Key.page_down,
            "insert": keyboard.Key.insert,
            "shift": keyboard.Key.shift,
            "shift_l": keyboard.Key.shift_l,
            "shift_r": keyboard.Key.shift_r,
            "ctrl": keyboard.Key.ctrl,
            "ctrl_l": keyboard.Key.ctrl_l,
            "ctrl_r": keyboard.Key.ctrl_r,
            "alt": keyboard.Key.alt,
            "alt_l": keyboard.Key.alt_l,
            "alt_r": keyboard.Key.alt_r,
            "cmd": keyboard.Key.cmd,
            "cmd_l": keyboard.Key.cmd_l,
            "cmd_r": keyboard.Key.cmd_r,
            "win": keyboard.Key.cmd,
            "caps_lock": keyboard.Key.caps_lock,
            "f1": keyboard.Key.f1,
            "f2": keyboard.Key.f2,
            "f3": keyboard.Key.f3,
            "f4": keyboard.Key.f4,
            "f5": keyboard.Key.f5,
            "f6": keyboard.Key.f6,
            "f7": keyboard.Key.f7,
            "f8": keyboard.Key.f8,
            "f9": keyboard.Key.f9,
            "f10": keyboard.Key.f10,
            "f11": keyboard.Key.f11,
            "f12": keyboard.Key.f12,
        }

        key_lower = key.lower().replace(" ", "_")
        if key_lower in special_keys:
            return special_keys[key_lower]

        if len(key) == 1:
            return keyboard.KeyCode.from_char(key)

        return None

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

        for key in list(self.key_state.keys()):
            if self.key_state.get(key, False):
                try:
                    key_obj = self._parse_key(key)
                    if key_obj:
                        self.keyboard_controller.release(key_obj)
                except Exception:
                    pass
                self.key_state[key] = False

        self.logger.debug("Released all buttons and keys")
