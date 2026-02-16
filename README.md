# OpenTouch-Remote

**🚀 A high-performance DXGI Windows mirroring engine. AI-born, ready for human engineering.**

`dxgi` • `desktop-duplication` • `low-latency-streaming` • `remote-touch` • `high-fps-mirroring` • `no-app-required` • `windows-remote-control` • `ai-born` • `fastapi` • `socket-io` • `dxcam`

## 🚀 Features

- **Native Resolution Mirroring**: Streams your desktop at its full native resolution (1080p, 1440p, or 4K) directly to your mobile browser.
- **DXGI Screen Capture**: Powered by `dxcam` for ultra-high-FPS (up to 60fps) mirroring using the Windows Desktop Duplication API.
- **Intelligent Backpressure Protection**: Dynamically skips frames if the network is congested, preventing synchronization crashes and ensuring a smooth stream.
- **Adaptive Quality Control**: Automatically adjusts JPEG quality based on network latency for optimal performance.
- **Low Latency**: Binary frame transmission and high-speed WebSockets via `python-socketio`.
- **High-DPI Support**: Automatically scales touch inputs to match high-density mobile displays and Windows DPI settings.
- **Mobile Touch Translation**:
  - **Tap**: Left Click
  - **Long Press**: Right Click
  - **Drag**: Accurate hardware-level dragging
  - **Two-Finger Scroll**: Vertical scrolling matching mobile patterns.
- **Virtual Keyboard**: On-screen keyboard for common keys (ESC, Tab, Enter, Arrow keys, etc.).
- **QR Code Pairing**: Automatically displays a scannable QR code in your terminal for instant connection.
- **Multi-Monitor Support**: Select which monitor to capture via CLI.
- **Connection Quality Indicator**: Real-time latency display and quality bar.

## 🛠️ Requirements

- **OS**: Windows (Required for DXGI capture)
- **Python**: 3.11+
- **Toolchain**: [uv](https://github.com/astral-sh/uv) (Recommended)

## 📦 Installation

1. Clone or download the repository.
2. Ensure you have `uv` installed.
3. Sync dependencies:
   ```bash
   uv sync
   ```

## 🚦 How to Run

Simply run the following command in your terminal or double-click `run.bat`:

```bash
uv run main.py
```

1. The terminal will clear and display a **QR Code**.
2. Scan the QR code with your phone (must be on the same Wi-Fi network).
3. Start controlling your PC!

### ⚙️ CLI Options

```bash
uv run main.py --help

Options:
  --port, -p INT         Server port (default: 8000)
  --fps, -f INT          Target FPS 10-60 (default: 30)
  --quality, -q FLOAT    JPEG quality 0.1-1.0 (default: 0.85)
  --monitor, -m INT      Monitor index to capture (default: 0)
  --verbose, -v          Enable debug logging
  --host STR             Host to bind (default: 0.0.0.0)

Examples:
  uv run main.py                        Start with defaults
  uv run main.py --port 9000            Use port 9000
  uv run main.py --fps 60 --quality 0.9 High performance mode
  uv run main.py --monitor 1            Capture second monitor
  uv run main.py --verbose              Enable debug logging
```

## 🎮 Interface Controls

- **Fullscreen Button**: Toggle mobile browser fullscreen mode.
- **Keyboard Button**: Toggle on-screen keyboard.
- **Reset Button**: Refresh the connection if the stream stutters.
- **FPS Counter**: Monitor your connection performance in real-time.
- **Latency Indicator**: Shows current network latency in milliseconds.
- **Quality Bar**: Visual indicator of stream quality.

## ⚠️ Security Note

This application is designed for **trusted local networks only**. Both your PC and mobile device must be on the same Wi-Fi network. Do not expose the server to the public internet.

---

## 📺 Watch it in Action

If you want to see more high-performance technical showcases and development logic:

[**▶️ Visit the AmiXDme YouTube Channel**](https://www.youtube.com/@AmiXDme)

---

## 📄 License

This project is licensed under the [Apache License 2.0](LICENSE).

---

*Built with FastAPI, Socket.IO, pynput, and DXcam.*