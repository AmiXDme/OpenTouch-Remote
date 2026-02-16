import threading
import time
import cv2
import numpy as np
from typing import Optional, Callable
import dxcam
import logging

from .config import Config


class CaptureEngine:
    def __init__(self, config: Config):
        self.config = config
        self.target_fps = config.target_fps
        self.base_jpeg_quality = int(config.jpeg_quality * 100)
        self.current_jpeg_quality = self.base_jpeg_quality
        self.monitor_idx = config.monitor_idx
        self.camera: Optional[dxcam.DXCamera] = None
        self.running = False
        self.capture_thread: Optional[threading.Thread] = None
        self.frame_callback: Optional[Callable[[bytes], None]] = None
        self.lock = threading.Lock()
        self.desktop_width = 0
        self.desktop_height = 0
        self.logger = logging.getLogger("opentouch.capture")

        self.last_frame: Optional[np.ndarray] = None
        self.frame_diff_threshold = 0.02
        self.skip_identical_frames = True

        self.stats = {
            "frames_captured": 0,
            "frames_skipped": 0,
            "frames_sent": 0,
        }

    def start(self, frame_callback: Callable[[bytes], None]):
        with self.lock:
            if self.running:
                return
            self.frame_callback = frame_callback
            try:
                self.camera = dxcam.create(
                    device_idx=self.monitor_idx, output_idx=0, output_color="BGR"
                )
                self.camera.start(target_fps=self.target_fps)
                self.running = True
                self.desktop_width, self.desktop_height = self.get_desktop_size()
                self.logger.info(
                    f"Capture started on monitor {self.monitor_idx} "
                    f"({self.desktop_width}x{self.desktop_height} @ {self.target_fps}fps)"
                )
                self.capture_thread = threading.Thread(
                    target=self._capture_loop, daemon=True
                )
                self.capture_thread.start()
            except Exception as e:
                self.logger.error(f"Failed to start capture: {e}")
                raise

    def stop(self):
        with self.lock:
            self.running = False
            if self.camera:
                try:
                    self.camera.stop()
                    self.camera.release()
                except Exception:
                    pass
                self.camera = None
            self.logger.info(f"Capture stopped. Stats: {self.stats}")

    def get_desktop_size(self) -> tuple[int, int]:
        import ctypes

        try:
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()
            return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        except Exception:
            return 1920, 1080

    def set_target_resolution(self, width: int, height: int):
        pass

    def set_quality(self, quality: float):
        self.current_jpeg_quality = max(30, min(100, int(quality * 100)))
        self.logger.debug(f"Quality adjusted to {self.current_jpeg_quality}%")

    def get_stats(self) -> dict:
        return self.stats.copy()

    def _capture_loop(self):
        last_frame_time = 0.0
        frame_interval = 1.0 / self.target_fps
        consecutive_identical = 0

        while self.running:
            try:
                now = time.time()
                if now - last_frame_time < frame_interval:
                    time.sleep(0.001)
                    continue

                if self.camera is None:
                    time.sleep(0.01)
                    continue

                frame = self.camera.get_latest_frame()
                self.stats["frames_captured"] += 1

                if frame is not None:
                    if self.skip_identical_frames and self.last_frame is not None:
                        if self._frames_identical(frame, self.last_frame):
                            consecutive_identical += 1
                            self.stats["frames_skipped"] += 1
                            if consecutive_identical < 5:
                                time.sleep(0.001)
                                continue

                    consecutive_identical = 0
                    processed = self._process_frame(frame)
                    if processed and self.frame_callback:
                        self.frame_callback(processed)
                        self.stats["frames_sent"] += 1
                        last_frame_time = now
                        self.last_frame = frame.copy()
                else:
                    time.sleep(0.001)
            except Exception as e:
                self.logger.debug(f"Capture loop error: {e}")
                time.sleep(0.01)

    def _frames_identical(self, frame1: np.ndarray, frame2: np.ndarray) -> bool:
        if frame1.shape != frame2.shape:
            return False
        diff = np.abs(frame1.astype(np.int16) - frame2.astype(np.int16))
        change_ratio = np.mean(diff) / 255.0
        return change_ratio < self.frame_diff_threshold

    def _process_frame(self, frame: np.ndarray) -> Optional[bytes]:
        try:
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.current_jpeg_quality]
            _, buffer = cv2.imencode(".jpg", frame, encode_params)
            return buffer.tobytes()
        except Exception as e:
            self.logger.debug(f"Frame processing error: {e}")
            return None
