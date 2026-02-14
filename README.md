# OpenTouch-Remote

**🚀 A high-performance DXGI Windows mirroring engine. AI-born, ready for human engineering.**

`dxgi` • `desktop-duplication` • `low-latency-streaming` • `remote-touch` • `high-fps-mirroring` • `no-app-required` • `windows-remote-control` • `ai-born` • `fastapi` • `socket-io` • `dxcam`

## 🚀 Features

- **Native Resolution Mirroring**: Streams your desktop at its full native resolution (1080p, 1440p, or 4K) directly to your mobile browser.
- **DXGI Screen Capture**: Powered by `dxcam` for ultra-high-FPS (up to 60fps) mirroring using the Windows Desktop Duplication API.
- **Intelligent Backpressure Protection**: Dynamically skips frames if the network is congested, preventing synchronization crashes and ensuring a smooth stream.
- **Low Latency**: Binary frame transmission and high-speed WebSockets via `python-socketio`.
- **High-DPI Support**: Automatically scales touch inputs to match high-density mobile displays and Windows DPI settings.
- **Mobile Touch Translation**:
  - **Tap**: Left Click
  - **Long Press**: Right Click
  - **Drag**: Accurate hardware-level dragging
  - **Two-Finger Scroll**: Vertical scrolling matching mobile patterns.
- **QR Code Pairing**: Automatically displays a scannable QR code in your terminal for instant connection.

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

## 🎮 Interface Controls

- **Fullscreen Button**: Toggle mobile browser fullscreen mode.
- **Reset Button**: Refresh the connection if the stream stutters.
- **FPS Counter**: Monitor your connection performance in real-time.

---
*Built with FastAPI, Socket.IO, pynput, and DXcam.*
