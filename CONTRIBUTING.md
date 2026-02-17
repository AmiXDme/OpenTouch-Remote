# ⚔️ Contributing to OpenTouch-Remote

So, you've decided to venture into the world of low-latency Windows mirroring. Welcome, brave developer. We're building the fastest, smoothest remote touch interface known to mankind (or at least, to your local network).

This isn't your average "fix a typo" repo. We deal in raw socket frames, binary streams, and milliseconds. **If you slow it down, you're out.**

---

## 🎭 The Standard

We operate on a simple philosophy:
1.  **Speed is King.** If your PR adds latency, it better calculate Pi while I wait.
2.  **Code is Art.** Ugly code will be mocked, then rejected.
3.  **No bloated dependencies.** We serve raw pixels, not NPM packages.

---

## 🛠️ The Setup

We use **[uv](https://github.com/astral-sh/uv)** because `pip` is too slow for us. If you don't have it, go get it. We'll wait... (not really).

### 1. Clone the Repository
```bash
git clone https://github.com/AmiXDme/OpenTouch-Remote.git
cd OpenTouch-Remote
```

### 2. Sync Dependencies
```bash
uv sync
```

### 3. Start the Engine
```bash
uv run main.py
```
*If a QR code appears, you have succeeded. If it crashes, read the error message before you cry in the issues.*

---

## 📜 The Rules (Coding Standards)

Violate these, and the CI (or I) will reject you.

### 🐍 Python
-   **Type Hints are Warning Labels**: Use them. `def foo(d: dict)` is lazy. `def foo(d: Dict[str, Any])` is professional.
-   **Async Everything**: We use `FastAPI` and `Socket.IO`. If you use `time.sleep()`, remove yourself from the premises. Use `await asyncio.sleep()`.
-   **PEP 8**: Follow it. We're professionals, not amateurs.

### 🔒 The Frontend Monolith
The entire frontend lives inside a massive HTML string in `src/server.py`.
-   **Yes, it's a string.**
-   **Yes, it's painful.**
-   **Deal with it.**
If you edit the HTML/JS/CSS, **test it on a real phone**. Desktop simulations lie.

### 🧪 The Tests
We have tests. You should run them.
```bash
uv run pytest
```
*If you submit a PR with failing tests, I will close it with a meme.*

---

## 🚀 Submission Protocol

### 1. Branching
Create a branch that describes your mission.
-   `feat/add-4k-support` (Good)
-   `fix/latency-bug` (Good)
-   `my-changes` (Bad - straight to jail)

### 2. Commits
We speak **Conventional Commits**.
-   `feat: add new gesture support`
-   `fix: resolve jpeg artifacting`
-   `perf: reduce latency by 2ms`
-   `docs: fix my terrible grammar`

### 3. Pull Request
-   **Title**: Clear and concise.
-   **Description**: Tell me *why* you did this. "Fixed stuff" is not a description.
-   **Evidence**: If it's a UI change, show a screenshot. If it's a performance boost, show the benchmarks.

---

## 🤝 Community

If you're stuck, confused, or just want to show off:
-   Check the [Issues](https://github.com/AmiXDme/OpenTouch-Remote/issues) tab.
-   Don't ask "how do I run python". Ask "why is the DXGI capture buffer overflowing on high-DPI scaling?"

**Now go forth and code.**
