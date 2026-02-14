import threading
import time
import cv2
import numpy as np
from typing import Optional, Callable
import dxcam


class CaptureEngine:
    def __init__(self, target_fps: int = 30, jpeg_quality: float = 0.8):
        self.target_fps = target_fps
        self.jpeg_quality = int(jpeg_quality * 100)
        self.camera: Optional[dxcam.DXCamera] = None
        self.running = False
        self.capture_thread: Optional[threading.Thread] = None
        self.frame_callback: Optional[Callable[[bytes], None]] = None
        self.lock = threading.Lock()
        self.desktop_width = 0
        self.desktop_height = 0
        self.target_width = 1280
        self.target_height = 720

    def start(self, frame_callback: Callable[[bytes], None]):
        with self.lock:
            if self.running:
                return
            self.frame_callback = frame_callback
            # Re-create camera to ensure fresh state, targeting primary monitor explicitly
            self.camera = dxcam.create(device_idx=0, output_idx=0, output_color="BGR")
            self.camera.start(target_fps=self.target_fps)
            self.running = True
            self.desktop_width, self.desktop_height = self.get_desktop_size()
            self.capture_thread = threading.Thread(
                target=self._capture_loop, daemon=True
            )
            self.capture_thread.start()

    def stop(self):
        with self.lock:
            self.running = False
            if self.camera:
                self.camera.stop()
                self.camera.release()
                self.camera = None

    def get_desktop_size(self) -> tuple[int, int]:
        import ctypes

        try:
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()  # Ensure we get the real resolution, not scaled
            return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        except Exception:
            # Fallback to a common default if all else fails
            return 1920, 1080

    def set_target_resolution(self, width: int, height: int):
        # We now ignore the mobile viewport scaling to maintain monitor-native size
        # but we keep the method for compatibility
        pass

    def _capture_loop(self):
        last_frame_time = 0.0
        frame_interval = 1.0 / self.target_fps

        while self.running:
            try:
                now = time.time()
                if now - last_frame_time < frame_interval:
                    time.sleep(0.001)
                    continue

                frame = self.camera.get_latest_frame()
                if frame is not None:
                    processed = self._process_frame(frame)
                    if processed and self.frame_callback:
                        self.frame_callback(processed)
                        last_frame_time = now
                else:
                    time.sleep(0.001)
            except Exception:
                time.sleep(0.01)

    def _process_frame(self, frame: np.ndarray) -> Optional[bytes]:
        try:
            # We skip the resizing completely to maintain MONIOR-SIZE quality
            # Only encode to JPEG at high quality
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality]
            _, buffer = cv2.imencode(".jpg", frame, encode_params)
            return buffer.tobytes()
        except Exception:
            return None
