import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from src.config import Config
from src.capture_engine import CaptureEngine
from src.input_handler import InputHandler
from src.network_utils import get_local_ip, get_available_port
from src.qr_display import generate_qr_terminal


class TestConfig:
    def test_config_defaults(self):
        config = Config()
        assert config.port == 8000
        assert config.target_fps == 30
        assert config.jpeg_quality == 0.85
        assert config.monitor_idx == 0
        assert config.verbose is False

    def test_config_custom(self):
        config = Config(port=9000, target_fps=60, jpeg_quality=0.9)
        assert config.port == 9000
        assert config.target_fps == 60
        assert config.jpeg_quality == 0.9


class TestCaptureEngine:
    def test_capture_engine_init(self):
        config = Config(target_fps=30, jpeg_quality=0.8)
        engine = CaptureEngine(config)
        assert engine.target_fps == 30
        assert engine.base_jpeg_quality == 80
        assert engine.running is False

    def test_get_desktop_size_fallback(self):
        config = Config()
        engine = CaptureEngine(config)

        import ctypes

        user32 = ctypes.windll.user32
        expected_width = user32.GetSystemMetrics(0)
        expected_height = user32.GetSystemMetrics(1)

        width, height = engine.get_desktop_size()
        assert width == expected_width
        assert height == expected_height

    def test_process_frame(self):
        config = Config()
        engine = CaptureEngine(config)

        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        result = engine._process_frame(frame)

        assert result is not None
        assert isinstance(result, bytes)

    def test_set_quality(self):
        config = Config()
        engine = CaptureEngine(config)

        engine.set_quality(0.5)
        assert engine.current_jpeg_quality == 50

        engine.set_quality(1.5)
        assert engine.current_jpeg_quality == 100

        engine.set_quality(0.2)
        assert engine.current_jpeg_quality == 30

    def test_get_stats(self):
        config = Config()
        engine = CaptureEngine(config)

        stats = engine.get_stats()
        assert "frames_captured" in stats
        assert "frames_skipped" in stats
        assert "frames_sent" in stats


class TestInputHandler:
    def test_input_handler_init(self):
        handler = InputHandler()
        assert handler.desktop_width == 1920
        assert handler.desktop_height == 1080

    def test_set_desktop_size(self):
        handler = InputHandler()
        handler.set_desktop_size(2560, 1440)
        assert handler.desktop_width == 2560
        assert handler.desktop_height == 1440

    def test_transform_coordinates(self):
        handler = InputHandler()
        handler.set_desktop_size(1920, 1080)

        pc_x, pc_y = handler._transform_coordinates(640, 360, 1280, 720)
        assert pc_x == 960
        assert pc_y == 540

    def test_transform_coordinates_clamped(self):
        handler = InputHandler()
        handler.set_desktop_size(1920, 1080)

        pc_x, pc_y = handler._transform_coordinates(2000, 1000, 1280, 720)
        assert 0 <= pc_x < 1920
        assert 0 <= pc_y < 1080

    def test_parse_special_key(self):
        handler = InputHandler()

        from pynput import keyboard

        assert handler._parse_key("Enter") == keyboard.Key.enter
        assert handler._parse_key("escape") == keyboard.Key.esc
        assert handler._parse_key("Tab") == keyboard.Key.tab

    def test_parse_char_key(self):
        handler = InputHandler()

        result = handler._parse_key("a")
        assert result is not None

        result = handler._parse_key("A")
        assert result is not None


class TestNetworkUtils:
    def test_get_local_ip_returns_string(self):
        ip = get_local_ip()
        assert isinstance(ip, str)
        assert len(ip) > 0

    def test_get_available_port_returns_int(self):
        port = get_available_port(8000)
        assert isinstance(port, int)
        assert port >= 8000
        assert port < 8100


class TestQRDisplay:
    def test_generate_qr_terminal(self):
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

        config = Config(port=8000)
        server = OpenTouchServer(config)

        assert server.config.port == 8000
        assert server.capture_engine is not None
        assert server.input_handler is not None

    def test_html_page_not_empty(self):
        from src.server import OpenTouchServer

        config = Config()
        server = OpenTouchServer(config)
        html = server._get_html_page()

        assert len(html) > 0
        assert "<canvas" in html
        assert "socket.io" in html
        assert "keyboard-bar" in html

    def test_quality_controller(self):
        from src.server import QualityController

        qc = QualityController(base_quality=0.85)
        assert qc.get_quality() == 0.85

        qc.record_latency(300)
        assert qc.get_quality() < 0.85

        qc.record_latency(20)
        qc.record_latency(20)
        qc.record_latency(20)
