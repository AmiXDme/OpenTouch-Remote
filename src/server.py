import asyncio
import json
from typing import Dict, Optional, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import socketio

from .capture_engine import CaptureEngine
from .input_handler import InputHandler
from .qr_display import display_connection_info
from .network_utils import get_local_ip, get_available_port


class OpenTouchServer:
    def __init__(self, port: int = 8000, target_fps: int = 30):
        self.port = port
        self.target_fps = target_fps
        self.app = FastAPI(title="OpenTouch-Remote")
        self.sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
        self.socket_app = socketio.ASGIApp(self.sio, self.app)

        self.capture_engine = CaptureEngine(target_fps=target_fps)
        self.input_handler = InputHandler()

        self.connected_clients: Dict[str, Dict[str, Any]] = {}
        self.client_resolutions: Dict[str, tuple] = {}
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.is_broadcasting = False  # Backpressure flag

        self._setup_routes()
        self._setup_socket_events()

    def _setup_routes(self):
        @self.app.get("/", response_class=HTMLResponse)
        async def index():
            return self._get_html_page()

        @self.app.get("/health")
        async def health():
            return {"status": "healthy"}

    def _setup_socket_events(self):
        @self.sio.event
        async def connect(sid, environ, auth=None):
            # Capture the ACTUAL running loop used by uvicorn
            if self.loop is None or self.loop.is_closed():
                self.loop = asyncio.get_running_loop()

            self.connected_clients[sid] = {
                "connected_at": asyncio.get_event_loop().time()
            }
            print(f"Client connected: {sid}")

            if len(self.connected_clients) == 1:
                desktop_size = self.capture_engine.get_desktop_size()
                self.input_handler.set_desktop_size(desktop_size[0], desktop_size[1])

                def frame_callback(frame_data: bytes):
                    # Skip frame if we are still busy sending the previous one
                    if self.is_broadcasting:
                        return

                    # Safely dispatch from producer thread to uvicorn loop
                    asyncio.run_coroutine_threadsafe(
                        self._broadcast_frame(frame_data), self.loop
                    )

                self.capture_engine.start(frame_callback)

            await self.sio.emit(
                "connected",
                {"desktop_size": list(self.capture_engine.get_desktop_size())},
                to=sid,
            )

        @self.sio.event
        async def disconnect(sid):
            print(f"Client disconnected: {sid}")

            if sid in self.connected_clients:
                del self.connected_clients[sid]
            if sid in self.client_resolutions:
                del self.client_resolutions[sid]

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
                print(f"Input error: {e}")

    async def _broadcast_frame(self, frame_data: bytes):
        if self.connected_clients:
            self.is_broadcasting = True
            try:
                await self.sio.emit("frame", frame_data)
            except Exception as e:
                print(f"Broadcast error: {e}")
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

        @keyframes fadeIn {
            from { opacity: 0; transform: translate(-50%, -10px); }
            to { opacity: 1; transform: translate(-50%, 0); }
        }

        /* Gestures Indicator */
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
    </div>

    <div id="gesture-hint">
        Tap: Click • Hold: Right Click • 2 Fingers: Scroll
    </div>

    <div class="controls">
        <div class="btn" id="btn-fullscreen">
            <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/></svg>
        </div>
        <div class="btn" id="btn-reset">
            <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
        </div>
    </div>
    
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        const status = document.getElementById('status');
        const dot = document.getElementById('dot');
        const fpsCounter = document.getElementById('fps-counter');
        
        let socket = null;
        let desktopWidth = 1920;
        let desktopHeight = 1080;
        let frameCount = 0;
        let lastFpsUpdate = Date.now();
        
        // Touch State
        let touchStartPos = null;
        let touchStartTime = 0;
        let isDragging = false;
        let longPressTimer = null;
        let isRightClick = false;
        
        // Scroll State
        let lastTwoFingerDist = null;
        let lastTwoFingerCenter = null;

        function connect() {
            socket = io(window.location.origin, {
                transports: ['websocket']
            });
            
            socket.on('connect', () => {
                status.textContent = 'Connected';
                dot.style.background = '#22c55e';
                dot.style.boxShadow = '0 0 10px #22c55e';
                reportViewport();
            });
            
            socket.on('connected', (data) => {
                desktopWidth = data.desktop_size[0];
                desktopHeight = data.desktop_size[1];
            });
            
            socket.on('frame', (data) => {
                const blob = new Blob([data], { type: 'image/jpeg' });
                const url = URL.createObjectURL(blob);
                const img = new Image();
                img.onload = () => {
                    if (canvas.width !== img.width || canvas.height !== img.height) {
                        canvas.width = img.width;
                        canvas.height = img.height;
                        reportViewport(); // Re-report after canvas size change
                    }
                    ctx.drawImage(img, 0, 0);
                    URL.revokeObjectURL(url);
                    frameCount++;
                    updateFps();
                };
                img.src = url;
            });
            
            socket.on('disconnect', () => {
                status.textContent = 'Disconnected';
                dot.style.background = '#ef4444';
                dot.style.boxShadow = '0 0 10px #ef4444';
            });
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
            
            // Map touch coordinate to CANVAS coordinate
            const x = (touch.clientX - rect.left) * (canvas.width / rect.width);
            const y = (touch.clientY - rect.top) * (canvas.height / rect.height);
            
            return { x, y };
        }

        function sendInput(type, data) {
            if (socket && socket.connected) {
                socket.emit('input', { type, ...data });
            }
        }

        // Logic for Clicks vs Drags
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
                    // Provide haptic feedback if available
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

        document.getElementById('btn-reset').addEventListener('click', () => {
            window.location.reload();
        });

        window.addEventListener('resize', reportViewport);
        
        connect();
    </script>
</body>
</html>"""

    def run(self, host: str = "0.0.0.0", port: Optional[int] = None):
        import uvicorn

        actual_port = port or get_available_port(self.port)
        local_ip = get_local_ip()
        url = f"http://{local_ip}:{actual_port}"

        display_connection_info(url)

        uvicorn.run(self.socket_app, host=host, port=actual_port, log_level="warning")
