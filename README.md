# OpenTouch-Remote

**🚀 The Apex of Windows Mirroring. AI-Architected. Human-Engineered.**

Zero bloat. Zero app stores. Just raw **DXGI** performance delivered straight to your browser.

`dxgi` • `desktop-duplication` • `low-latency` • `remote-touch` • `60fps` • `no-install`

---

## ⚡ The Power

Stop using sluggish remote desktop tools. OpenTouch-Remote is built for **speed**.

-   **DXGI Capture Core**: Powered by `dxcam`, tapping directly into the Windows GPU pipeline. If it's on your screen, it's on your phone. Instantly.
-   **Intelligent Backpressure**: The engine monitors network congestion in real-time. If your WiFi lags, we drop frames to keep the input responsive. We never crash; we adapt.
-   **Adaptive Quality**: We calculate latency milliseconds. If the network struggles, we compress harder. If it clears, we give you pristine 4K.
-   **Binary WebSockets**: We don't send base64 strings like amateurs. We blast raw binary JPEGs for maximum throughput.
-   **Translation Layer**:
    -   **Tap** -> Left Click
    -   **Hold** -> Right Click
    -   **Drag** -> Hardware Mouse Drag
    -   **Two-Finger** -> Native Scroll
-   **No App Required**: It's just a web page. But it feels like native code.

---

## 🛠️ The Gear (Requirements)

-   **OS**: Windows (DXGI is a Windows exclusive).
-   **Python**: 3.11+
-   **Manager**: [uv](https://github.com/astral-sh/uv) (Recommended for speed).

---

## 🚀 Ignition (Installation)

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/AmiXDme/OpenTouch-Remote.git
    cd OpenTouch-Remote
    ```

2.  **Sync Dependencies**:
    ```bash
    uv sync
    ```

3.  **Launch**:
    ```bash
    uv run main.py
    ```
    *Scan the QR code. Control your PC. Done.*

---

## 🎮 CLI Options

Power users don't click icons. They use flags.

```bash
uv run main.py --help

Options:
  --port, -p INT         Server port (default: 8000)
  --fps, -f INT          Force target FPS 10-60 (default: 30)
  --quality, -q FLOAT    Set JPEG quality 0.1-1.0 (default: 0.85)
  --monitor, -m INT      Select monitor index (default: 0)
  --verbose, -v          Enable debug logging
```

---

## ⚔️ Contributing

Think you can make it faster? Prove it.
Read our **[CONTRIBUTING.md](CONTRIBUTING.md)** before you submit a PR. We have strict standards for performance.

---

## 📺 Witness the Performance

See the development logic and showcases:
[**▶️ Visit the AmiXDme YouTube Channel**](https://www.youtube.com/@AmiXDme)

---

## 📄 License

Apache License 2.0. Open source, open power.

---

*Built with FastAPI, Socket.IO, pynput, and DXcam.*