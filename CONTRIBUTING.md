# ⚔️ Protocol for Contributors

Welcome to the pursuit of zero latency. We're building the fastest Windows mirroring engine in the Python ecosystem. If you're here to optimize, you're in the right place. If you're here to bloat, you're not.

This project is built on **raw DXGI frames** and **asynchronous event loops**. We don't do "good enough." We do "fastest possible."

---

## 🎭 The Standard

1.  **Latency is the Enemy.** Any change that adds a single millisecond of overhead without a massive feature trade-off will be rejected.
2.  **Logic is Clean.** We don't use nested "if" statements when a guard clause will do. We use Type Hints because we aren't amateurs.
3.  **Dependencies are Weight.** Every new package in `pyproject.toml` is a burden. If you can write it in 5 lines of NumPy, don't import a library.

---

## 🛠️ The Workspace

We use **[uv](https://github.com/astral-sh/uv)**. It is non-negotiable.

### 1. Preparation
```bash
git clone https://github.com/AmiXDme/OpenTouch-Remote.git
cd OpenTouch-Remote
uv sync
```

### 2. Validation
Before you even think about a Pull Request, run the tests.
```bash
uv run pytest
```
*A failing test is a mark of poor planning. Fix it or don't submit.*

---

## 📜 The Code (Engineering Standards)

### 🐍 Python Backend
-   **Async First**: We use `FastAPI` and `python-socketio`. Never block the event loop. If you need a long-running process, use a thread (like our `CaptureEngine`) and bridge it with `asyncio.run_coroutine_threadsafe`.
-   **Buffer Management**: We deal with raw bytes. Be careful with memory copies. Use `.copy()` only when necessary.
-   **Math over Loops**: If you're processing pixels, use **NumPy**. If I see a `for` loop iterating over pixels, I will close the PR immediately.

### 🔒 The Frontend Monolith
The UI lives in `src/server.py` as a raw HTML/JS string.
-   **Why?** Because we value single-binary feel and zero-configuration deployments.
-   **The Rule**: Keep the JS fast. Avoid heavy frameworks. Use Vanilla JS and CSS variables. If it stutters on a mobile device, it fails the test.

---

## 🚀 Submission Protocol

### 1. Branching
`feat/`, `fix/`, or `perf/`. If your branch name is `patch-1`, you're doing it wrong.

### 2. Commits
Use **Conventional Commits**.
-   `perf: optimize jpeg encoding via opencv` (Excellent)
-   `fix: move mouse clamping to handle high-dpi` (Excellent)
-   `fixed stuff` (Reject)

### 3. Benchmarks
If you claim a performance boost, **show the numbers**. Use the built-in `/stats` endpoint to prove your change reduced frame-skip or latency.

---

## 🤝 Community

If you have a technical question about the DXGI pipeline or touch scaling, open an Issue. If you're asking how to install Python, use a search engine. We value your time; value ours.

**Now, go find some milliseconds.**
