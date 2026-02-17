# OpenTouch-Remote

**🚀 The Apex of Windows Mirroring. AI-Architected. Human-Engineered.**

Zero bloat. Zero lag. Just raw **DXGI** performance delivered straight to your browser. This isn't just a screen share; it's a high-frequency synchronization engine designed for those who demand immediate response.

`dxgi` • `desktop-duplication` • `low-latency` • `remote-touch` • `60fps` • `no-install`

---

## ⚡ The Power

Stop using sluggish remote desktop tools that feel like moving through mud. OpenTouch-Remote is built for **speed**.

-   **DXGI Capture Core**: Powered by `dxcam`, tapping directly into the Windows GPU pipeline. We don't ask the OS for permission; we take the frames from the buffer.
-   **Intelligent Backpressure**: Our engine monitors network congestion every millisecond. If your signal drops, we skip frames to keep the interaction live. We don't buffer; we adapt.
-   **Static Frame Suppression**: We calculate pixel-diffs between frames. If the screen hasn't changed, we don't send anything. Effortless efficiency.
-   **DPI-Aware Scaling**: We handle Windows High-DPI settings natively. Your touch translates to the exact pixel, no matter how much you've scaled your 4K display.
-   **Latency-Linked Quality**: Dynamic JPEG compression that breathes with your network. Excellent signal? Pristine pixels. Poor signal? Sharp speed.
-   **Zero-App Interface**:
    -   **Tap** -> Precise Left Click
    -   **Long Press** -> Contextual Right Click
    -   **Two-Finger Slide** -> Natural Scroll Physics
    -   **Hardware Drag** -> Seamless window management

---

## 🛠️ The Gear (Requirements)

-   **OS**: Windows (Required for the DXGI pipeline. No exceptions).
-   **Python**: 3.11+
-   **Manager**: [uv](https://github.com/astral-sh/uv) (We standardise on `uv` for its superior dependency resolution speed).

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
    *Scan the QR code. Take control. That's it.*

---

## 🎮 CLI Mastery

Control the engine with flags. Don't be basic.

```bash
uv run main.py --help

Options:
  --port, -p INT         Server port (default: 8000)
  --fps, -f INT          Aggressive FPS target 10-60 (default: 30)
  --quality, -q FLOAT    Base JPEG quality 0.1-1.0 (default: 0.85)
  --monitor, -m INT      Target monitor index (0 = primary)
  --verbose, -v          Show raw engine logs
```

---

## ⚔️ Contributing

Think you can find an extra 2ms of performance? We want to see it.
Read our **[CONTRIBUTING.md](CONTRIBUTING.md)** before you touch the code. We have standards.

---

## 📺 Witness the Logic

High-performance technical showcases and development deep-dives:
[**▶️ Visit the AmiXDme YouTube Channel**](https://www.youtube.com/@AmiXDme)

---

## 📄 License

Apache License 2.0. Clean, open, powerful.

---

*Built with FastAPI, Socket.IO, pynput, and DXcam.*