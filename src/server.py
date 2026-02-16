import asyncio
import json
import time
from typing import Dict, Optional, Any, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import socketio
import logging

from .capture_engine import CaptureEngine
from .input_handler import InputHandler
from .qr_display import display_connection_info
from .network_utils import get_local_ip, get_available_port
from .config import Config


class QualityController:
    def __init__(self, base_quality: float):
        self.base_quality = base_quality
        self.current_quality = base_quality
        self.latency_samples: List[float] = []
        self.max_samples = 10
        self.min_quality = 0.4
        self.max_quality = 1.0
        self.low_latency_threshold = 50
        self.high_latency_threshold = 200
        self.logger = logging.getLogger("opentouch.quality")

    def record_latency(self, latency_ms: float):
        self.latency_samples.append(latency_ms)
        if len(self.latency_samples) > self.max_samples:
            self.latency_samples.pop(0)
        self._adjust_quality()

    def _adjust_quality(self):
        if len(self.latency_samples) < 3:
            return

        avg_latency = sum(self.latency_samples) / len(self.latency_samples)

        if avg_latency < self.low_latency_threshold:
            target = min(self.base_quality + 0.1, self.max_quality)
        elif avg_latency > self.high_latency_threshold:
            target = max(self.base_quality - 0.2, self.min_quality)
        else:
            target = self.base_quality

        if abs(target - self.current_quality) > 0.05:
            self.current_quality = target
            self.logger.debug(
                f"Quality adjusted to {self.current_quality:.2f} (latency: {avg_latency:.0f}ms)"
            )

    def get_quality(self) -> float:
        return self.current_quality

    def get_avg_latency(self) -> float:
        if not self.latency_samples:
            return 0
        return sum(self.latency_samples) / len(self.latency_samples)


class OpenTouchServer:
    def __init__(self, config: Config):
        self.config = config
        self.port = config.port
        self.app = FastAPI(title="OpenTouch-Remote")
        self.sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
        self.socket_app = socketio.ASGIApp(self.sio, self.app)

        self.capture_engine = CaptureEngine(config)
        self.input_handler = InputHandler()
        self.quality_controller = QualityController(config.jpeg_quality)

        self.connected_clients: Dict[str, Dict[str, Any]] = {}
        self.client_resolutions: Dict[str, tuple] = {}
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.is_broadcasting = False
        self.logger = logging.getLogger("opentouch.server")

        self.latency_tracker: Dict[str, Dict[str, float]] = {}

        self._setup_routes()
        self._setup_socket_events()

    def _setup_routes(self):
        @self.app.get("/", response_class=HTMLResponse)
        async def index():
            return self._get_html_page()

        @self.app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "clients": len(self.connected_clients),
                "quality": self.quality_controller.get_quality(),
                "stats": self.capture_engine.get_stats(),
            }

        @self.app.get("/stats")
        async def stats():
            return {
                "connected_clients": len(self.connected_clients),
                "quality": {
                    "current": self.quality_controller.get_quality(),
                    "base": self.quality_controller.base_quality,
                    "avg_latency_ms": self.quality_controller.get_avg_latency(),
                },
                "capture": self.capture_engine.get_stats(),
            }

    def _setup_socket_events(self):
        @self.sio.event
        async def connect(sid, environ, auth=None):
            if self.loop is None or self.loop.is_closed():
                self.loop = asyncio.get_running_loop()

            self.connected_clients[sid] = {"connected_at": time.time()}
            self.latency_tracker[sid] = {
                "last_ping": time.time(),
                "last_pong": time.time(),
            }
            self.logger.info(f"Client connected: {sid}")

            if len(self.connected_clients) == 1:
                desktop_size = self.capture_engine.get_desktop_size()
                self.input_handler.set_desktop_size(desktop_size[0], desktop_size[1])

                def frame_callback(frame_data: bytes):
                    if self.is_broadcasting:
                        return

                    if self.loop is not None:
                        asyncio.run_coroutine_threadsafe(
                            self._broadcast_frame(frame_data), self.loop
                        )

                self.capture_engine.start(frame_callback)

            await self.sio.emit(
                "connected",
                {
                    "desktop_size": list(self.capture_engine.get_desktop_size()),
                    "quality": self.quality_controller.get_quality(),
                },
                to=sid,
            )

        @self.sio.event
        async def disconnect(sid):
            self.logger.info(f"Client disconnected: {sid}")

            if sid in self.connected_clients:
                del self.connected_clients[sid]
            if sid in self.client_resolutions:
                del self.client_resolutions[sid]
            if sid in self.latency_tracker:
                del self.latency_tracker[sid]

            if not self.connected_clients:
                self.capture_engine.stop()
                self.input_handler.release_all()

        @self.sio.event
        async def viewport(sid, data):
            width = data.get("width", 1280)
            height = data.get("height", 720)
            self.client_resolutions[sid] = (width, height)
            self.capture_engine.set_target_resolution(width, height)

        @self.sio.event
        async def input(sid, data):
            if sid not in self.client_resolutions:
                return

            client_w, client_h = self.client_resolutions[sid]

            try:
                self.input_handler.process_event(data, client_w, client_h)
            except Exception as e:
                self.logger.error(f"Input error: {e}")

        @self.sio.event
        async def pong(sid, data):
            if sid in self.latency_tracker:
                now = time.time()
                latency_ms = (now - self.latency_tracker[sid]["last_ping"]) * 1000
                self.latency_tracker[sid]["last_pong"] = now

                self.quality_controller.record_latency(latency_ms)
                current_quality = self.quality_controller.get_quality()

                if (
                    abs(
                        current_quality - self.capture_engine.current_jpeg_quality / 100
                    )
                    > 0.05
                ):
                    self.capture_engine.set_quality(current_quality)

                await self.sio.emit(
                    "latency",
                    {
                        "ms": round(latency_ms, 1),
                        "quality": current_quality,
                    },
                    to=sid,
                )

    async def _broadcast_frame(self, frame_data: bytes):
        if self.connected_clients:
            self.is_broadcasting = True
            try:
                await self.sio.emit("frame", frame_data)
            except Exception as e:
                self.logger.error(f"Broadcast error: {e}")
            finally:
                self.is_broadcasting = False

    def _get_html_page(self) -> str:
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>OpenTouch Remote</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&family=JetBrains+Mono&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0a0a0c;
            --accent: #3b82f6;
            --accent-glow: rgba(59, 130, 246, 0.4);
            --text: #f8fafc;
            --glass: rgba(255, 255, 255, 0.05);
            --glass-border: rgba(255, 255, 255, 0.1);
            --quality-excellent: #22c55e;
            --quality-good: #84cc16;
            --quality-fair: #eab308;
            --quality-poor: #ef4444;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
        
        body { 
            width: 100vw; height: 100vh; 
            overflow: hidden; 
            background: var(--bg); 
            color: var(--text);
            font-family: 'Outfit', sans-serif;
            touch-action: none;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        #container {
            position: relative;
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: radial-gradient(circle at center, #1e293b 0%, #0a0a0c 100%);
        }

        #canvas {
            box-shadow: 0 20px 50px rgba(0,0,0,0.5);
            background: #000;
            max-width: 100%;
            max-height: 100%;
            transition: opacity 0.3s ease;
        }

        .overlay {
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            padding: 8px 16px;
            background: var(--glass);
            backdrop-filter: blur(12px);
            border: 1px solid var(--glass-border);
            border-radius: 100px;
            display: flex;
            align-items: center;
            gap: 12px;
            z-index: 100;
            pointer-events: none;
            opacity: 0;
            animation: fadeIn 0.5s ease forwards 0.5s;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            background: #22c55e;
            border-radius: 50%;
            box-shadow: 0 0 10px #22c55e;
        }

        .status-text {
            font-size: 13px;
            font-weight: 500;
            letter-spacing: 0.02em;
        }

        #fps-counter {
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            color: #94a3b8;
        }

        #latency-indicator {
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            padding: 2px 6px;
            border-radius: 4px;
            background: rgba(34, 197, 94, 0.2);
            color: var(--quality-excellent);
        }

        .controls {
            position: fixed;
            bottom: 30px;
            right: 30px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            z-index: 100;
        }

        .btn {
            width: 50px;
            height: 50px;
            border-radius: 16px;
            background: var(--glass);
            backdrop-filter: blur(12px);
            border: 1px solid var(--glass-border);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            transition: all 0.2s ease;
            pointer-events: auto;
        }

        .btn:active {
            transform: scale(0.9);
            background: var(--accent);
            border-color: var(--accent);
        }

        .btn-secondary {
            width: 44px;
            height: 44px;
            border-radius: 12px;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translate(-50%, -10px); }
            to { opacity: 1; transform: translate(-50%, 0); }
        }

        #gesture-hint {
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 12px;
            color: #64748b;
            text-align: center;
            padding: 8px 20px;
            background: rgba(0,0,0,0.3);
            border-radius: 20px;
            pointer-events: none;
        }

        .keyboard-bar {
            position: fixed;
            bottom: 100px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            justify-content: center;
            max-width: 90vw;
            z-index: 100;
            opacity: 0;
            transition: opacity 0.3s ease;
            pointer-events: none;
        }

        .keyboard-bar.visible {
            opacity: 1;
            pointer-events: auto;
        }

        .key-btn {
            min-width: 44px;
            height: 36px;
            padding: 0 12px;
            border-radius: 8px;
            background: var(--glass);
            backdrop-filter: blur(12px);
            border: 1px solid var(--glass-border);
            color: white;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.15s ease;
        }

        .key-btn:active {
            background: var(--accent);
            border-color: var(--accent);
            transform: scale(0.95);
        }

        .quality-bar {
            position: fixed;
            top: 60px;
            left: 50%;
            transform: translateX(-50%);
            width: 150px;
            height: 4px;
            background: rgba(255,255,255,0.1);
            border-radius: 2px;
            overflow: hidden;
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .quality-bar.visible {
            opacity: 1;
        }

        .quality-fill {
            height: 100%;
            background: var(--quality-excellent);
            transition: width 0.3s ease, background 0.3s ease;
        }
    </style>
</head>
<body>
    <div id="container">
        <canvas id="canvas"></canvas>
    </div>

    <div class="overlay">
        <div class="status-dot" id="dot"></div>
        <div class="status-text" id="status">Connecting...</div>
        <div id="fps-counter">0 FPS</div>
        <div id="latency-indicator">0ms</div>
    </div>

    <div class="quality-bar" id="quality-bar">
        <div class="quality-fill" id="quality-fill"></div>
    </div>

    <div id="gesture-hint">
        Tap: Click | Hold: Right Click | 2 Fingers: Scroll
    </div>

    <div class="controls">
        <div class="btn" id="btn-fullscreen" title="Fullscreen">
            <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/></svg>
        </div>
        <div class="btn btn-secondary" id="btn-keyboard" title="Keyboard">
            <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="2" y="6" width="20" height="12" rx="2"/><path d="M6 10h.01M10 10h.01M14 10h.01M18 10h.01M8 14h8"/></svg>
        </div>
        <div class="btn btn-secondary" id="btn-reset" title="Reset">
            <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
        </div>
    </div>

    <div class="keyboard-bar" id="keyboard-bar">
        <div class="key-btn" data-key="Escape">ESC</div>
        <div class="key-btn" data-key="Tab">TAB</div>
        <div class="key-btn" data-key="Enter">ENTER</div>
        <div class="key-btn" data-key="Backspace">DEL</div>
        <div class="key-btn" data-key="Arrow_Up">UP</div>
        <div class="key-btn" data-key="Arrow_Down">DOWN</div>
        <div class="key-btn" data-key="Arrow_Left">LEFT</div>
        <div class="key-btn" data-key="Arrow_Right">RIGHT</div>
        <div class="key-btn" data-key=" ">SPACE</div>
        <div class="key-btn" data-key="Control">CTRL</div>
        <div class="key-btn" data-key="Alt">ALT</div>
        <div class="key-btn" data-key="Shift">SHIFT</div>
    </div>
    
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        const status = document.getElementById('status');
        const dot = document.getElementById('dot');
        const fpsCounter = document.getElementById('fps-counter');
        const latencyIndicator = document.getElementById('latency-indicator');
        const qualityBar = document.getElementById('quality-bar');
        const qualityFill = document.getElementById('quality-fill');
        const keyboardBar = document.getElementById('keyboard-bar');
        
        let socket = null;
        let desktopWidth = 1920;
        let desktopHeight = 1080;
        let frameCount = 0;
        let lastFpsUpdate = Date.now();
        let currentQuality = 0.85;
        
        let touchStartPos = null;
        let touchStartTime = 0;
        let isDragging = false;
        let longPressTimer = null;
        let isRightClick = false;
        
        let lastTwoFingerDist = null;
        let lastTwoFingerCenter = null;

        let activeKeys = new Set();

        function connect() {
            socket = io(window.location.origin, {
                transports: ['websocket']
            });
            
            socket.on('connect', () => {
                status.textContent = 'Connected';
                dot.style.background = '#22c55e';
                dot.style.boxShadow = '0 0 10px #22c55e';
                qualityBar.classList.add('visible');
                reportViewport();
                startPing();
            });
            
            socket.on('connected', (data) => {
                desktopWidth = data.desktop_size[0];
                desktopHeight = data.desktop_size[1];
                currentQuality = data.quality || 0.85;
                updateQualityDisplay();
            });
            
            socket.on('frame', (data) => {
                const blob = new Blob([data], { type: 'image/jpeg' });
                const url = URL.createObjectURL(blob);
                const img = new Image();
                img.onload = () => {
                    if (canvas.width !== img.width || canvas.height !== img.height) {
                        canvas.width = img.width;
                        canvas.height = img.height;
                        reportViewport();
                    }
                    ctx.drawImage(img, 0, 0);
                    URL.revokeObjectURL(url);
                    frameCount++;
                    updateFps();
                };
                img.src = url;
            });
            
            socket.on('latency', (data) => {
                latencyIndicator.textContent = `${data.ms}ms`;
                currentQuality = data.quality;
                updateQualityDisplay();
            });
            
            socket.on('disconnect', () => {
                status.textContent = 'Disconnected';
                dot.style.background = '#ef4444';
                dot.style.boxShadow = '0 0 10px #ef4444';
                qualityBar.classList.remove('visible');
            });
        }

        function startPing() {
            setInterval(() => {
                if (socket && socket.connected) {
                    socket.emit('pong', { ts: Date.now() });
                }
            }, 1000);
        }

        function updateQualityDisplay() {
            const percentage = currentQuality * 100;
            qualityFill.style.width = `${percentage}%`;
            
            let color = '#22c55e';
            if (currentQuality < 0.5) color = '#ef4444';
            else if (currentQuality < 0.7) color = '#eab308';
            else if (currentQuality < 0.85) color = '#84cc16';
            
            qualityFill.style.background = color;
            latencyIndicator.style.background = `${color}33`;
            latencyIndicator.style.color = color;
        }

        function updateFps() {
            const now = Date.now();
            if (now - lastFpsUpdate >= 1000) {
                fpsCounter.textContent = `${frameCount} FPS`;
                frameCount = 0;
                lastFpsUpdate = now;
            }
        }

        function reportViewport() {
            if (socket && socket.connected) {
                const dpr = window.devicePixelRatio || 1;
                socket.emit('viewport', {
                    width: Math.floor(window.innerWidth * dpr),
                    height: Math.floor(window.innerHeight * dpr),
                    viewWidth: window.innerWidth,
                    viewHeight: window.innerHeight
                });
            }
        }

        function getTouchPos(e) {
            const rect = canvas.getBoundingClientRect();
            const touch = e.touches[0] || e.changedTouches[0];
            const x = (touch.clientX - rect.left) * (canvas.width / rect.width);
            const y = (touch.clientY - rect.top) * (canvas.height / rect.height);
            return { x, y };
        }

        function sendInput(type, data) {
            if (socket && socket.connected) {
                socket.emit('input', { type, ...data });
            }
        }

        canvas.addEventListener('touchstart', (e) => {
            e.preventDefault();
            if (e.touches.length === 1) {
                const pos = getTouchPos(e);
                touchStartPos = pos;
                touchStartTime = Date.now();
                isDragging = false;
                isRightClick = false;

                longPressTimer = setTimeout(() => {
                    isRightClick = true;
                    if (window.navigator.vibrate) window.navigator.vibrate(50);
                }, 600);
            } else if (e.touches.length === 2) {
                const t1 = e.touches[0];
                const t2 = e.touches[1];
                lastTwoFingerCenter = {
                    x: (t1.clientX + t2.clientX) / 2,
                    y: (t1.clientY + t2.clientY) / 2
                };
            }
        }, { passive: false });

        canvas.addEventListener('touchmove', (e) => {
            e.preventDefault();
            if (e.touches.length === 1) {
                const pos = getTouchPos(e);
                const dist = Math.sqrt(Math.pow(pos.x - touchStartPos.x, 2) + Math.pow(pos.y - touchStartPos.y, 2));
                
                if (dist > 5) {
                    if (longPressTimer) clearTimeout(longPressTimer);
                    if (!isDragging) {
                        sendInput('mousedown', { button: 'left' });
                        isDragging = true;
                    }
                    sendInput('move', { x: pos.x, y: pos.y });
                }
            } else if (e.touches.length === 2) {
                const t1 = e.touches[0];
                const t2 = e.touches[1];
                const center = {
                    x: (t1.clientX + t2.clientX) / 2,
                    y: (t1.clientY + t2.clientY) / 2
                };
                
                const dy = center.y - lastTwoFingerCenter.y;
                const dx = center.x - lastTwoFingerCenter.x;
                
                if (Math.abs(dy) > 2 || Math.abs(dx) > 2) {
                    sendInput('scroll', { dx: -dx, dy: dy });
                    lastTwoFingerCenter = center;
                }
            }
        }, { passive: false });

        canvas.addEventListener('touchend', (e) => {
            e.preventDefault();
            if (longPressTimer) clearTimeout(longPressTimer);

            if (e.touches.length === 0) {
                if (isRightClick) {
                    const pos = getTouchPos(e);
                    sendInput('move', { x: pos.x, y: pos.y });
                    sendInput('click', { button: 'right' });
                } else if (!isDragging) {
                    const pos = getTouchPos(e);
                    sendInput('move', { x: pos.x, y: pos.y });
                    sendInput('click', { button: 'left' });
                } else {
                    sendInput('mouseup', { button: 'left' });
                }
                isDragging = false;
            }
        }, { passive: false });

        document.getElementById('btn-fullscreen').addEventListener('click', () => {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen();
            } else {
                document.exitFullscreen();
            }
        });

        document.getElementById('btn-keyboard').addEventListener('click', () => {
            keyboardBar.classList.toggle('visible');
        });

        document.getElementById('btn-reset').addEventListener('click', () => {
            window.location.reload();
        });

        document.querySelectorAll('.key-btn').forEach(btn => {
            const key = btn.dataset.key;
            
            btn.addEventListener('touchstart', (e) => {
                e.preventDefault();
                if (!activeKeys.has(key)) {
                    activeKeys.add(key);
                    sendInput('keydown', { key });
                    btn.style.background = 'var(--accent)';
                }
            });
            
            btn.addEventListener('touchend', (e) => {
                e.preventDefault();
                if (activeKeys.has(key)) {
                    activeKeys.delete(key);
                    sendInput('keyup', { key });
                    btn.style.background = '';
                }
            });
        });

        document.addEventListener('keydown', (e) => {
            if (!activeKeys.has(e.key)) {
                activeKeys.add(e.key);
                sendInput('keydown', { key: e.key });
            }
        });

        document.addEventListener('keyup', (e) => {
            if (activeKeys.has(e.key)) {
                activeKeys.delete(e.key);
                sendInput('keyup', { key: e.key });
            }
        });

        window.addEventListener('resize', reportViewport);
        
        connect();
    </script>
</body>
</html>"""

    def run(self, host: Optional[str] = None, port: Optional[int] = None):
        import uvicorn

        actual_host = host or self.config.host
        actual_port = port or get_available_port(self.config.port)
        local_ip = get_local_ip()
        url = f"http://{local_ip}:{actual_port}"

        self.logger.info(
            f"Starting OpenTouch-Remote server on {actual_host}:{actual_port}"
        )
        display_connection_info(url)

        uvicorn.run(
            self.socket_app, host=actual_host, port=actual_port, log_level="warning"
        )
