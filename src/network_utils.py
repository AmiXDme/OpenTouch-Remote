import socket
import subprocess
import platform


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        pass

    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        if ip and not ip.startswith("127."):
            return ip
    except Exception:
        pass

    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ["ipconfig"], capture_output=True, text=True, timeout=5
            )
            lines = result.stdout.split("\n")
            for i, line in enumerate(lines):
                if "Wireless" in line or "Wi-Fi" in line or "Ethernet" in line:
                    for j in range(i, min(i + 10, len(lines))):
                        if "IPv4" in lines[j]:
                            ip = lines[j].split(":")[-1].strip()
                            return ip
    except Exception:
        pass

    return "127.0.0.1"


def get_available_port(start_port: int = 8000, max_attempts: int = 100) -> int:
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", port))
                return port
        except OSError:
            continue
    return start_port
