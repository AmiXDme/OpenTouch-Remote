# 🛡️ Security Policy: The Safeguard

In a system built for raw hardware access, security is a non-negotiable layer. We protect the system integrity of our users with the same precision we apply to our capture engine.

## 1. Supported Versions

We do not support legacy code. Security patches are only applied to the latest version of the `main` branch.

| Version | Status             |
| ------- | ------------------ |
| v0.2.x  | 🚀 Active Support |
| < v0.2  | 🛑 Discontinued    |

## 2. Architectural Bounds: LOCAL ONLY

OpenTouch-Remote is designed as a **Trusted Network Only** tool. 

-   **The Threat**: Exposing the server port (default `8000`) to the public internet allows anyone to view your screen and inject inputs.
-   **The Defense**: 
    -   Bind only to your local IP or `0.0.0.0` within a private firewall.
    -   Never port-forward this application.
    -   If you require remote access across the world, use a **VPN** or an **encrypted SSH tunnel**. This is the only acceptable method.

## 3. Vulnerability Disclosure

If you find a flaw in our handling of socket frames or input sanitation, follow the protocol:

1.  **Private Discovery**: Do not open a public Issue.
2.  **Notification**: Use GitHub's private reporting tool or contact the maintainers directly.
3.  **Details**: Provide the "How, What, and Why." Show us the exploit sequence and, more importantly, how to fix it.
4.  **Bounty**: Your reward is the respect of the community and a clean repository.

## 4. Input Sanitization
We sanitize coordinates and key inputs to prevent malicious execution, but we rely on the host OS security for process isolation. Ensure your Windows environment is updated.

---

**Prioritize the Safeguard. Keep the connection clean.**
