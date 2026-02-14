import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np


class TestCaptureEngine:
    def test_capture_engine_init(self):
        from src.capture_engine import CaptureEngine

        engine = CaptureEngine(target_fps=30, jpeg_quality=0.8)
        assert engine.target_fps == 30
        assert engine.jpeg_quality == 80
        assert engine.running is False

    def test_get_desktop_size_fallback(self):
        from src.capture_engine import CaptureEngine

        engine = CaptureEngine()

        import ctypes

        user32 = ctypes.windll.user32
        expected_width = user32.GetSystemMetrics(0)
        expected_height = user32.GetSystemMetrics(1)

        width, height = engine.get_desktop_size()
        assert width == expected_width
        assert height == expected_height

    def test_process_frame(self):
        from src.capture_engine import CaptureEngine

        engine = CaptureEngine()

        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        result = engine._process_frame(frame)

        assert result is not None
        assert isinstance(result, str)


class TestInputHandler:
    def test_input_handler_init(self):
        from src.input_handler import InputHandler

        handler = InputHandler()
        assert handler.desktop_width == 1920
        assert handler.desktop_height == 1080

    def test_set_desktop_size(self):
        from src.input_handler import InputHandler

        handler = InputHandler()
        handler.set_desktop_size(2560, 1440)
        assert handler.desktop_width == 2560
        assert handler.desktop_height == 1440

    def test_transform_coordinates(self):
        from src.input_handler import InputHandler

        handler = InputHandler()
        handler.set_desktop_size(1920, 1080)

        pc_x, pc_y = handler._transform_coordinates(640, 360, 1280, 720)
        assert pc_x == 960
        assert pc_y == 540

    def test_transform_coordinates_clamped(self):
        from src.input_handler import InputHandler

        handler = InputHandler()
        handler.set_desktop_size(1920, 1080)

        pc_x, pc_y = handler._transform_coordinates(2000, 1000, 1280, 720)
        assert 0 <= pc_x < 1920
        assert 0 <= pc_y < 1080


class TestNetworkUtils:
    def test_get_local_ip_returns_string(self):
        from src.network_utils import get_local_ip

        ip = get_local_ip()
        assert isinstance(ip, str)
        assert len(ip) > 0

    def test_get_available_port_returns_int(self):
        from src.network_utils import get_available_port

        port = get_available_port(8000)
        assert isinstance(port, int)
        assert port >= 8000
        assert port < 8100


class TestQRDisplay:
    def test_generate_qr_terminal(self):
        from src.qr_display import generate_qr_terminal

        output = generate_qr_terminal("http://192.168.1.1:8000", clear_screen=False)

        assert "OpenTouch-Remote" in output
        assert "http://192.168.1.1:8000" in output


class TestCoordinateTransformation:
    @pytest.mark.parametrize(
        "touch_x,touch_y,client_w,client_h,desktop_w,desktop_h,expected_x,expected_y",
        [
            (640, 360, 1280, 720, 1920, 1080, 960, 540),
            (0, 0, 1280, 720, 1920, 1080, 0, 0),
            (1280, 720, 1280, 720, 1920, 1080, 1919, 1079),
            (320, 180, 640, 360, 2560, 1440, 1280, 720),
        ],
    )
    def test_coordinate_math(
        self,
        touch_x,
        touch_y,
        client_w,
        client_h,
        desktop_w,
        desktop_h,
        expected_x,
        expected_y,
    ):
        from src.input_handler import InputHandler

        handler = InputHandler()
        handler.set_desktop_size(desktop_w, desktop_h)

        pc_x, pc_y = handler._transform_coordinates(
            touch_x, touch_y, client_w, client_h
        )

        assert abs(pc_x - expected_x) <= 1
        assert abs(pc_y - expected_y) <= 1


class TestServerLifecycle:
    def test_server_init(self):
        from src.server import OpenTouchServer

        server = OpenTouchServer(port=8000)

        assert server.port == 8000
        assert server.capture_engine is not None
        assert server.input_handler is not None

    def test_html_page_not_empty(self):
        from src.server import OpenTouchServer

        server = OpenTouchServer()
        html = server._get_html_page()

        assert len(html) > 0
        assert "<canvas" in html
        assert "socket.io" in html
